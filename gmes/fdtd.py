#!/usr/bin/env python

from copy import deepcopy
from threading import Thread, Lock
from numpy.lib.index_tricks import ndindex
from numpy import arange

from geometric import GeomBoxTree
from file_io import write_hdf5, snapshot
from show import ShowLine, ShowPlane
from pointwise_material import DummyEx, DummyEy, DummyEz
from pointwise_material import DummyHx, DummyHy, DummyHz
import constants


class TimeStep:
    """Store the current time-step(n) and time(t).
    """
    
    def __init__(self, n=0, t=0.0):
        self.n = n
        self.t = t
        
        
class FDTD:
    """three dimensional finite-difference time-domain class
    """
    
    def __init__(self, space=None, geom_list=None, src_list=None, verbose=True):
        self.lock_ex, self.lock_ey, self.lock_ez = Lock(), Lock(), Lock()
        self.lock_hx, self.lock_hy, self.lock_hz = Lock(), Lock(), Lock()
        self.lock_fig = Lock()

        self.fig_id = 0
        
        self.space = space
        
        self.geom_list = deepcopy(geom_list)
        for geom_obj in self.geom_list:
            geom_obj.init(self.space)
            
        self.dx, self.dy, self.dz = space.dx, space.dy, space.dz
        self.dt = space.dt
        self.time_step = TimeStep()
        
        if verbose is True:
            print "Generating geometric binary search tree."
        self.geom_tree = GeomBoxTree(self.geom_list)

        self.src_list = deepcopy(src_list)
        for so in self.src_list:
            so.init(self.geom_tree, self.space)
                    
        if verbose is True:
            print "Allocating memory for the electric & magnetic fields."
            
        # electric & magnetic field storages
        self.ex = space.get_ex_storage()
        self.ey = space.get_ey_storage()
        self.ez = space.get_ez_storage()
        self.hx = space.get_hx_storage()
        self.hy = space.get_hy_storage()
        self.hz = space.get_hz_storage()

        if verbose is True:
            print "Allocating memory for the material data."
        # propagation medium information for electric & magnetic fields
        self.material_ex = space.get_material_ex_storage()
        self.material_ey = space.get_material_ey_storage()
        self.material_ez = space.get_material_ez_storage()
        self.material_hx = space.get_material_hx_storage()
        self.material_hy = space.get_material_hy_storage()
        self.material_hz = space.get_material_hz_storage()
        
        if verbose is True:
            print "Mapping the material data."
        self.init_material()
        
        if verbose is True:
            print "Mapping the source information."
        self.init_source()

        #Thread(target=Tk().mainloop).start()
        
    def init_material_ex(self):
        """Set up the update mechanism for Ex field and stores the result
        at self.material_ex.
        """
        
        self.lock_ex.acquire()
        shape = self.ex.shape
        for idx in ndindex(shape[0], shape[1], shape[2]):
            if idx[1] == shape[1] - 1 or idx[2] == shape[2] - 1:
                self.material_ex[idx] = DummyEx(idx, 1)
            else:
                co = self.space.ex_index_to_space(idx)
                geom_obj = self.geom_tree.object_of_point(co)
                self.material_ex[idx] = geom_obj.material.get_pointwise_material_ex(idx, co)
        self.lock_ex.release()
                        
    def init_material_ey(self):
        """Set up the update mechanism for Ey field and stores the result
        at self.material_ex.
        """
        
        self.lock_ey.acquire()
        shape = self.ey.shape
        for idx in ndindex(shape[0], shape[1], shape[2]):
            if idx[2] == shape[2] - 1 or idx[0] == shape[0] - 1:
                self.material_ey[idx] = DummyEy(idx, 1)
            else:
                co = self.space.ey_index_to_space(idx)
                geom_obj = self.geom_tree.object_of_point(co)
                self.material_ey[idx] = geom_obj.material.get_pointwise_material_ey(idx, co)
        self.lock_ey.release()
        
    def init_material_ez(self):
        """Set up the update mechanism for Ez field and stores the result
        at self.material_ex.
        """
        
        self.lock_ez.acquire()
        shape = self.ez.shape
        for idx in ndindex(shape[0], shape[1], shape[2]):
            if idx[0] == shape[0] - 1 or idx[1] == shape[1] - 1:
                self.material_ez[idx] = DummyEz(idx, 1)
            else:
                co = self.space.ez_index_to_space(idx)
                geom_obj = self.geom_tree.object_of_point(co)
                self.material_ez[idx] = geom_obj.material.get_pointwise_material_ez(idx, co)
        self.lock_ez.release()
        
    def init_material_hx(self):
        """Set up the update mechanism for Hx field and stores the result
        at self.material_hx.
        """
        
        self.lock_hx.acquire()
        shape = self.hx.shape
        for idx in ndindex(shape[0], shape[1], shape[2]):
            if idx[1] == 0 or idx[2] == 0:
                self.material_hx[idx] = DummyHx(idx, 1)
            else:
                co = self.space.hx_index_to_space(idx)
                geom_obj = self.geom_tree.object_of_point(co)
                self.material_hx[idx] = geom_obj.material.get_pointwise_material_hx(idx, co)
        self.lock_hx.release()
                                            
    def init_material_hy(self):
        """Set up the update mechanism for Hy field and stores the result
        at self.material_hy.
        """
        
        self.lock_hy.acquire()
        shape = self.hy.shape
        for idx in ndindex(shape[0], shape[1], shape[2]):
            if idx[2] == 0 or idx[0] == 0:
                self.material_hy[idx] = DummyHy(idx, 1)
            else:
                co = self.space.hy_index_to_space(idx)
                geom_obj = self.geom_tree.object_of_point(co)
                self.material_hy[idx] = geom_obj.material.get_pointwise_material_hy(idx, co)
        self.lock_hy.release()
                                
    def init_material_hz(self):
        """Set up the update mechanism for Hz field and stores the result
        at self.material_ex.
        """
        
        self.lock_hz.acquire()
        shape = self.hz.shape
        for idx in ndindex(shape[0], shape[1], shape[2]):
            if idx[0] == 0 or idx[1] == 0:
                self.material_hz[idx] = DummyHz(idx, 1)
            else:
                co = self.space.hz_index_to_space(idx)
                geom_obj = self.geom_tree.object_of_point(co)
                self.material_hz[idx] = geom_obj.material.get_pointwise_material_hz(idx, co)
        self.lock_hz.release()
        
    def init_material(self):       
        threads = []
        threads.append(Thread(target=self.init_material_ex))
        threads.append(Thread(target=self.init_material_ey))
        threads.append(Thread(target=self.init_material_ez))
        threads.append(Thread(target=self.init_material_hx))
        threads.append(Thread(target=self.init_material_hy))
        threads.append(Thread(target=self.init_material_hz))
                            
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
    
    def init_source_ex(self):
        for so in self.src_list:
            so.set_pointwise_source_ex(self.material_ex, self.space)
                
    def init_source_ey(self):
        for so in self.src_list:
            so.set_pointwise_source_ey(self.material_ey, self.space)
                
    def init_source_ez(self):
        for so in self.src_list:
            so.set_pointwise_source_ez(self.material_ez, self.space)
    
    def init_source_hx(self):
        for so in self.src_list:
            so.set_pointwise_source_hx(self.material_hx, self.space)
                
    def init_source_hy(self):
        for so in self.src_list:
            so.set_pointwise_source_hy(self.material_hy, self.space)
                
    def init_source_hz(self):
        for so in self.src_list:
            so.set_pointwise_source_hz(self.material_hz, self.space)
                            
    def init_source(self):
        threads = []
        threads.append(Thread(target=self.init_source_ex))
        threads.append(Thread(target=self.init_source_ey))
        threads.append(Thread(target=self.init_source_ez))
        threads.append(Thread(target=self.init_source_hx))
        threads.append(Thread(target=self.init_source_hy))
        threads.append(Thread(target=self.init_source_hz))
        
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
        
    def update_ex(self):
        self.lock_ex.acquire()
        for mo in self.material_ex.flat:
            mo.update(self.ex, self.hz, self.hy, self.dt, self.dy, self.dz)
        self.lock_ex.release()

    def update_ey(self):
        self.lock_ey.acquire()
        for mo in self.material_ey.flat:
            mo.update(self.ey, self.hx, self.hz, self.dt, self.dz, self.dx)
        self.lock_ey.release()
       
    def update_ez(self):
        self.lock_ez.acquire()
        for mo in self.material_ez.flat:
            mo.update(self.ez, self.hy, self.hx, self.dt, self.dx, self.dy)
        self.lock_ez.release()
              
    def update_hx(self):
        self.lock_hx.acquire()
        for mo in self.material_hx.flat:
            mo.update(self.hx, self.ez, self.ey, self.dt, self.dy, self.dz)
        self.lock_hx.release()
        
    def update_hy(self):
        self.lock_hy.acquire()
        for mo in self.material_hy.flat:
            mo.update(self.hy, self.ex, self.ez, self.dt, self.dz, self.dx)
        self.lock_hy.release()
                
    def update_hz(self):
        self.lock_hz.acquire()
        for mo in self.material_hz.flat:
            mo.update(self.hz, self.ey, self.ex, self.dt, self.dx, self.dy)
        self.lock_hz.release()
        
    def step(self):
        threads = []
        threads.append(Thread(target=self.update_ex))
        threads.append(Thread(target=self.update_ey))
        threads.append(Thread(target=self.update_ez))
        threads.append(Thread(target=self.write_hx))
        threads.append(Thread(target=self.write_hy))
        threads.append(Thread(target=self.write_hz))
                    
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()

        self.time_step.n += .5
        self.time_step.t = self.time_step.n * self.dt
        
        threads = []
        threads.append(Thread(target=self.update_hx))
        threads.append(Thread(target=self.update_hy))
        threads.append(Thread(target=self.update_hz))
        threads.append(Thread(target=self.write_ex))
        threads.append(Thread(target=self.write_ey))
        threads.append(Thread(target=self.write_ez))
                
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
            
        self.time_step.n += .5
        self.time_step.t = self.time_step.n * self.dt

    def show_line_ex(self, start, end, y_range=(-1,1), msecs=2500):
        title = 'Ex field'
        ylabel = 'displacement'
        
        start_idx = self.space.space_to_ex_index(start)
        end_idx = [i + 1 for i in self.space.space_to_ex_index(end)]
        
        if end_idx[0] - start_idx[0] > 1:
            y_data = self.ex[start_idx[0]:end_idx[0], start_idx[1], start_idx[2]]
        elif end_idx[1] - start_idx[1] > 1:
            y_data = self.ex[start_idx[0], start_idx[1]:end_idx[1], start_idx[2]]
        elif end_idx[2] - start_idx[2] > 1:
            y_data = self.ex[start_idx[0], start_idx[1], start_idx[2]:end_idx[2]]

        start2 = self.space.ex_index_to_space(start_idx)
        end2 = self.space.ex_index_to_space(end_idx)
        domain_idx = map(lambda x, y: x - y, end_idx, start_idx)
        for i in xrange(3):
            if domain_idx[i] != 1:
                if i == 0:
                    step = self.space.dx
                    xlabel = 'x'
                elif i == 1:
                    step = self.space.dy
                    xlabel = 'y'
                elif i == 2:
                    step = self.space.dz
                    xlabel = 'z'
                else:
                    pass
                break
        
        x_data = arange(start2[i], end2[i], step)
        
        if len(x_data) > len(y_data):
            x_data = x_data[:-1]
            
        showcase = ShowLine(x_data, y_data, y_range, self.time_step, xlabel, ylabel, title, msecs, self.fig_id)
        self.fig_id += 1
        showcase.start()
        
    def _show(self, component, axis, cut, amp_range, msecs, title):
        field = []
        
        if isinstance(axis, constants.X):
            if isinstance(component, constants.Ex):
                field = self.ex[cut, :, :]
                low = self.space.ex_index_to_space((0,0,0))
                high_idx = [i - 1 for i in self.ex.shape]
                high = self.space.ex_index_to_space(high_idx)
                cut = self.space.space_to_ex_index((cut, 0, 0))[0]
                
            elif isinstance(component, constants.Hx):
                field = self.hx[cut, :, :]
                low = self.space.hx_index_to_space((0,0,0))
                high_idx = [i - 1 for i in self.hx.shape]
                high = self.space.hx_index_to_space(high_idx)
                cut = self.space.space_to_hx_index((cut, 0, 0))[0]
                
            extent = (low[2], high[2], low[1], high[1])
            xlabel = 'z'
            ylabel = 'y'
            
        elif isinstance(axis, constants.Y):
            if isinstance(component, constants.Ey):
                field = self.ey[:, cut, :]
                low = self.space.ey_index_to_space((0,0,0))
                high_idx = [i - 1 for i in self.ey.shape]
                high = self.space.ey_index_to_space(high_idx)
                cut = self.space.space_to_ey_index((0, cut, 0))[1]
                
            elif isinstance(component, constants.Hy):
                field = self.hy[:, cut, :]
                low = self.space.hy_index_to_space((0,0,0))
                high_idx = [i - 1 for i in self.hy.shape]
                high = self.space.hy_index_to_space(high_idx)
                cut = self.space.space_to_hy_index((0, cut, 0))[1]
                
            extent = (low[2], high[2], low[0], high[0])
            xlabel = 'z'
            ylabel = 'x'
            
        elif isinstance(axis, constants.Z):
            if isinstance(component, constants.Ez):
                field = self.ez[:, :, cut]
                low = self.space.ez_index_to_space((0,0,0))
                high_idx = [i - 1 for i in self.ez.shape]
                high = self.space.ez_index_to_space(high_idx)
                cut = self.space.space_to_ez_index((0, 0, cut))[2]
                
            elif isinstance(component, constants.Hz):
                field = self.hz[:, :, cut]
                low = self.space.ez_index_to_space((0,0,0))
                high_idx = [i - 1 for i in self.hz.shape]
                high = self.space.hz_index_to_space(high_idx)
                cut = self.space.space_to_hz_index((0, 0, cut))[2]
                
            extent = (low[1], high[1], low[0], high[0])
            xlabel = 'y'
            ylabel = 'x'
            
        else:
            msg = "axis must be an instance of gmes.constants.Directional."
            raise ValueError(msg)

        showcase = ShowPlane(field, extent, amp_range, self.time_step, xlabel, ylabel, title, msecs, self.fig_id)
        self.fig_id += 1
        showcase.start()

    def show_ex(self, axis, cut, amp_range=(-1,1), msecs=2500):
        self._show(constants.Ex(), axis, cut, amp_range, msecs, 'Ex field')
        
    def show_ey(self, axis, cut, amp_range=(-1,1), msecs=2500):
        self._show(constants.Ey(), axis, cut, amp_range, msecs, 'Ey field')
        
    def show_ez(self, axis, cut, amp_range=(-1,1), msecs=2500):
        self._show(constants.Ez(), axis, cut, amp_range, msecs, 'Ez field')

    def show_hx(self, axis, cut, amp_range=(-1,1), msecs=2500):
        self._show(constants.Hx(), axis, cut, amp_range, msecs, 'Hx field')
        
    def show_hy(self, axis, cut, amp_range=(-1,1), msecs=2500):
        self._show(constants.Hy(), axis, cut, amp_range, msecs, 'Hy field')
        
    def show_hz(self, axis, cut, amp_range=(-1,1), msecs=2500):
        self._show(constants.Hz(), axis, cut, amp_range, msecs, 'Hz field')
        
    def write_ex(self, low=None, high=None, prefix=None, postfix=None):
        if low is None:
            low_idx = (0, 0, 0)
        else:
            low_idx = self.space.space_to_ex_index(low)
            
        if low is None:
            high_idx = self.ex.shape
        else:
            high_idx = self.space.space_to_ex_index(high)
        
        high_idx = [i + 1 for i in high_idx]
        
        name = ''
        if prefix is not None:
            name = prefix + name
        if postfix is not None:
            name = name + postfix
            
        write_hdf5(self.ex, name, low_idx, high_idx)
    
    def write_ey(self):
        pass
    
    def write_ez(self):
        pass

    def write_hx(self):
        pass
    
    def write_hy(self):
        pass
    
    def write_hz(self):
        pass
        
    def snapshot_ex(self, axis, cut):
        if axis == 'x':
            cut_idx = self.space.space_to_index((cut, 0, 0))[0]
            data = self.ex[cut_idx, :, :]
        elif axis == 'y':
            cut_idx = self.space.space_to_index((0, cut, 0))[1]
            data = self.ex[:, cut_idx, :]
        elif axis == 'z':
            cut_idx = self.space.space_to_index((0, 0, cut))[2]
            data = self.ex[:, :, cut_idx]
        else:
            pass
        
        filename = 't=' + str(self.time_step[1] * space.dt)
        snapshot(data, filename, 'ex')
        
    def snapshotEy(self, axis='z', cut=0, range=(-.1, .1), size=(400, 400)):
        pass
    
    def snapshotEz(self, axis='z', cut=0, range=(-.1, .1), size=(400, 400)):
        pass
    
    def snapshotHx(self, axis='z', cut=0, range=(-.1, .1), size=(400, 400)):
        pass
        
    def snapshotHy(self, axis='z', cut=0, range=(-.1, .1), size=(400, 400)):
        pass
        
    def snapshotHz(self, axis='z', cut=0, range=(-.1, .1), size=(400, 400)):
        pass
        

class TExFDTD(FDTD):
    """Two dimensional fdtd with transverse-electric mode with respect to x.
    
    Assume that the structure and incident wave is uniform in the x-direction.
    Just use Ey, Ez, and Hx field components the transverse-electric mode with respect to z.
    """
    
    def init_material(self):
        """Override FDTD.init_material().
        
        Initialize pointwise_material arrays only for Ey, Ez, and Hx field components.
        """
         
        threads = []
        threads.append(Thread(target=self.init_material_ey))
        threads.append(Thread(target=self.init_material_ez))
        threads.append(Thread(target=self.init_material_hx))
                            
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
    
    def init_source(self):
        """Override FDTD.init_source().
        
        Initialize pointwise_source in pointwise_material arrays only for Ey, Ez, and Hx field components.
        """
        
        threads = []
        threads.append(Thread(target=self.init_source_ey))
        threads.append(Thread(target=self.init_source_ez))
        threads.append(Thread(target=self.init_source_hx))
        
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
        
    def step(self):  
        """Override FDTD.step().
        
        Updates only Ey, Ez, and Hx field components.
        """
              
        threads = []
        threads.append(Thread(target=self.update_ey))
        threads.append(Thread(target=self.update_ez))
        
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()

        self.time_step.n += .5
        self.time_step.t = self.time_step.n * self.dt
        
        self.update_hx()

        self.time_step.n += .5
        self.time_step.t = self.time_step.n * self.dt
        
        
class TEyFDTD(FDTD):
    """Two dimensional fdtd which transverse-electric with respect to y.
    
    TEyFDTD updates only Ez, Ex, and Hy field.
    """
    
    def init_material(self):
        threads = []
        threads.append(Thread(target=self.init_material_ez))
        threads.append(Thread(target=self.init_material_ex))
        threads.append(Thread(target=self.init_material_hy))
                            
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
    
    def init_source(self):
        threads = []
        threads.append(Thread(target=self.init_source_ez))
        threads.append(Thread(target=self.init_source_ex))
        threads.append(Thread(target=self.init_source_hy))
        
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
            
    def step(self):        
        threads = []
        threads.append(Thread(target=self.update_ez))
        threads.append(Thread(target=self.update_ex))
        
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
            
        self.time_step.n += .5
        self.time_step.t = self.time_step.n * self.dt
        
        self.update_hy()

        self.time_step.n += .5
        self.time_step.t = self.time_step.n * self.dt
                
        
class TEzFDTD(FDTD):
    """
    two dimensional fdtd which transverse-electric with respect to z
    """
    
    def init_material(self):
        threads = []
        threads.append(Thread(target=self.init_material_ex))
        threads.append(Thread(target=self.init_material_ey))
        threads.append(Thread(target=self.init_material_hz))
                            
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
    
    def init_source(self):
        threads = []
        threads.append(Thread(target=self.init_source_ex))
        threads.append(Thread(target=self.init_source_ey))
        threads.append(Thread(target=self.init_source_hz))
        
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
            
    def step(self):
        threads = []
        threads.append(Thread(target=self.update_ex))
        threads.append(Thread(target=self.update_ey))
        
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()

        self.time_step.n += .5
        self.time_step.t = self.time_step.n * self.dt

        self.update_hz()
            
        self.time_step.n += .5
        self.time_step.t += self.dt
        
        
class TMxFDTD(FDTD):
    """
    two dimensional fdtd which transverse-magnetic with respect to x
    """
    
    def init_material(self):
        threads = []
        threads.append(Thread(target=self.init_material_hy))
        threads.append(Thread(target=self.init_material_hz))
        threads.append(Thread(target=self.init_material_ex))
                            
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
    
    def init_source(self):
        threads = []
        threads.append(Thread(target=self.init_source_hy))
        threads.append(Thread(target=self.init_source_hz))
        threads.append(Thread(target=self.init_source_ex))
        
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
            
    def step(self):
        self.update_ex()

        self.time_step.n += .5
        self.time_step.t = self.time_step.n * self.dt        

        threads = []
        threads.append(Thread(target=self.update_hy))
        threads.append(Thread(target=self.update_hz))
        
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()

        self.time_step.n += .5
        self.time_step.t = self.time_step.n * self.dt


class TMyFDTD(FDTD):
    """
    two dimensional fdtd which transverse-magnetic with respect to y
    """
    
    def init_material(self):
        threads = []
        threads.append(Thread(target=self.init_material_hz))
        threads.append(Thread(target=self.init_material_hx))
        threads.append(Thread(target=self.init_material_ey))
                            
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
    
    def init_source(self):
        threads = []
        threads.append(Thread(target=self.init_source_hz))
        threads.append(Thread(target=self.init_source_hx))
        threads.append(Thread(target=self.init_source_ey))
        
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
            
    def step(self):
        self.update_ey()
        
        self.time_step.n += .5
        self.time_step.t = self.time_step.n * self.dt
        
        threads = []
        threads.append(Thread(target=self.update_hz))        
        threads.append(Thread(target=self.update_hx))
        
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
            
        self.time_step.n += .5
        self.time_step.t = self.time_step.n * self.dt
        
                
class TMzFDTD(FDTD):
    """
    two dimensional fdtd which transverse-magnetic with respect to z
    """
    
    def init_material(self):
        threads = []
        threads.append(Thread(target=self.init_material_hx))
        threads.append(Thread(target=self.init_material_hy))
        threads.append(Thread(target=self.init_material_ez))
                            
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
    
    def init_source(self):
        threads = []
        threads.append(Thread(target=self.init_source_hx))
        threads.append(Thread(target=self.init_source_hy))
        threads.append(Thread(target=self.init_source_ez))
        
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
            
    def step(self):
        self.update_ez()

        self.time_step.n += .5
        self.time_step.t = self.time_step.n * self.dt
        
        threads = []
        threads.append(Thread(target=self.update_hx))
        threads.append(Thread(target=self.update_hy))
        
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()

        self.time_step.n += .5
        self.time_step.t = self.time_step.n * self.dt


class TEMxFDTD(FDTD):
    """
    y-polarized and x-directed one dimensional fdtd class
    """
    
    def init_material(self):
        threads = []
        threads.append(Thread(target=self.init_material_ey))
        threads.append(Thread(target=self.init_material_hz))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    def init_source(self):
        threads = []
        threads.append(Thread(target=self.init_source_ey))
        threads.append(Thread(target=self.init_source_hz))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    def step(self):
        self.update_ey()

        self.time_step.n += 5
        self.time_step.t = self.time_step.n * self.dt

        self.update_hz()

        self.time_step.n += 5
        self.time_step.t = self.time_step.n * self.dt
                
        
class TEMyFDTD(FDTD):
    """
    z-polarized and y-directed one dimensional fdtd class
    """
    
    def init_material(self):
        threads = []
        threads.append(Thread(target=self.init_material_ez))
        threads.append(Thread(target=self.init_material_hx))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    def init_source(self):
        threads = []
        threads.append(Thread(target=self.init_source_ez))
        threads.append(Thread(target=self.init_source_hx))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    def step(self):
        self.update_ez()

        self.time_step.n += 5
        self.time_step.t = self.time_step.n * self.dt

        self.update_hx()

        self.time_step.n += 5
        self.time_step.t = self.time_step.n * self.dt

        
class TEMzFDTD(FDTD):
    """
    x-polarized and z-directed one dimensional fdtd class
    """
    
    def init_material(self):
        threads = []
        threads.append(Thread(target=self.init_material_ex))
        threads.append(Thread(target=self.init_material_hy))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    def init_source(self):
        threads = []
        threads.append(Thread(target=self.init_source_ex))
        threads.append(Thread(target=self.init_source_hy))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    def step(self):
        self.update_ex()

        self.time_step.n += 5
        self.time_step.t = self.time_step.n * self.dt

        self.update_hy()

        self.time_step.n += 5
        self.time_step.t = self.time_step.n * self.dt
        
                
if __name__ == '__main__':
    from math import sin
    
    from numpy.core import inf
    
    from geometric import DefaultMaterial, Cylinder, Cartesian
    from material import Dielectric
    
    low = Dielectric(index=1)
    hi = Dielectric(index=3)
    width_hi = low.epsilon_r / (low.epsilon_r + hi.epsilon_r)
    space = Cartesian(size=[1, 1, 1])
    geom_list = [DefaultMaterial(material=low), Cylinder(material=hi, axis=[1, 0, 0], radius=inf, height=width_hi)]
    
    a = FDTD(space=space, geometry=geom_list)
    
    while True:
        a.step()
        a.ex[7, 7, 7] = sin(a.n)
        print a.n