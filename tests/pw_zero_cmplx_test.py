#!/usr/bin/env python

import os, sys
new_path = os.path.abspath('../')
sys.path.append(new_path)

import unittest
from gmes.pw_material import * 

    
class TestSequence(unittest.TestCase):
    def setUp(self):
        self.idx = (1,1,1)
        
        self.cmplxA = array(random.random((3,3,3)), complex)
        self.cmplxB = empty((3,3,3))
        self.cmplxC = empty((3,3,3))
        
        self.copyA = array(self.cmplxA)
        self.copyA[self.idx] = 0
        
        self.diff = 1
        
    def testEx(self):
        sampleCmplx = ZeroExCmplx(self.idx)
        sampleCmplx.update(self.cmplxA, self.cmplxB, self.cmplxC, 
                          self.diff, self.diff, self.diff)
        
        self.assertEqual((self.cmplxA == self.copyA).all(), True)
                         
    def testEy(self):
        sampleCmplx = ZeroEyCmplx(self.idx)
        sampleCmplx.update(self.cmplxA, self.cmplxB, self.cmplxC, 
                          self.diff, self.diff, self.diff)
        
        self.assertEqual((self.cmplxA == self.copyA).all(), True)
        
    def testEz(self):
        sampleCmplx = ZeroEzCmplx(self.idx)
        sampleCmplx.update(self.cmplxA, self.cmplxB, self.cmplxC, 
                          self.diff, self.diff, self.diff)
        
        self.assertEqual((self.cmplxA == self.copyA).all(), True)
        
    def testHx(self):
        sampleCmplx = ZeroHxCmplx(self.idx)
        sampleCmplx.update(self.cmplxA, self.cmplxB, self.cmplxC, 
                          self.diff, self.diff, self.diff)
        
        self.assertEqual((self.cmplxA == self.copyA).all(), True)
        
    def testHy(self):
        sampleCmplx = ZeroHyCmplx(self.idx)
        sampleCmplx.update(self.cmplxA, self.cmplxB, self.cmplxC, 
                          self.diff, self.diff, self.diff)
        
        self.assertEqual((self.cmplxA == self.copyA).all(), True)
        
    def testHz(self):
        sampleCmplx = ZeroHzCmplx(self.idx)
        sampleCmplx.update(self.cmplxA, self.cmplxB, self.cmplxC, 
                          self.diff, self.diff, self.diff)
        
        self.assertEqual((self.cmplxA == self.copyA).all(), True)
        
        
if __name__ == '__main__':
    unittest.main(argv=('', '-v'))
    