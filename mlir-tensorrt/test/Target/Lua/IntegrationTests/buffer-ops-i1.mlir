// REQUIRES: host-has-at-least-1-gpus
// RUN: mlir-tensorrt-opt %s -convert-memref-to-cuda -convert-plan-to-executor -convert-cuda-to-executor -executor-lowering-pipeline \
// RUN:   | mlir-tensorrt-translate -mlir-to-runtime-executable \
// RUN:   | mlir-tensorrt-runner -input-type=rtexe | FileCheck %s

!descriptor1D = !executor.table<!executor.ptr<device>, !executor.ptr<device>, index, index, index>
!hostMemRef = memref<4xi1, #plan.memory_space<host>>
!devMemRef = memref<4xi1, #plan.memory_space<device>>


memref.global @host_buffer : !hostMemRef = dense<0>
memref.global @cuda_buffer : !devMemRef = dense<0>

func.func @main() -> i32{
  %c0 = arith.constant 0 : i32
  %c0_index = arith.constant 0 : index
  %c1 = arith.constant 1 : i32
  %c1_index = arith.constant 1 : index
  %c4 = arith.constant 4 : index
  %c16 = arith.constant 16 : index

  %num_cuda_devices = cuda.num_devices : i32
  %has_cuda_device = arith.cmpi sge, %num_cuda_devices, %c1 : i32

  executor.print "found %d cuda devices"(%num_cuda_devices : i32)

  %0 = scf.if %has_cuda_device -> i32 {
    executor.print "start!"()
    %host_memref = memref.get_global @host_buffer: !hostMemRef
    %device_memref = memref.get_global @cuda_buffer: !devMemRef

    %c1b = arith.constant 1 : i1

    // Fill the host buffer.
    scf.for %i = %c0_index to %c4 step %c1_index {
       %ld = memref.load %host_memref[%i] : !hostMemRef
       %x = executor.bitwise_ori %ld, %c1b : i1
       memref.store %x, %host_memref[%i] : !hostMemRef
    }

    // Copy host -> device then device -> host
    memref.copy %host_memref , %device_memref : !hostMemRef to !devMemRef
    memref.copy %device_memref , %host_memref : !devMemRef to !hostMemRef
    // Deallocate
    memref.dealloc %device_memref : !devMemRef

    // Print the host buffer
    scf.for %i = %c0_index to %c4 step %c1_index {
      %value = memref.load %host_memref[%i] : !hostMemRef
      executor.print "host_memref[%i] = %d"(%i, %value : index, i1)
    }

    executor.print "done!"()
    scf.yield %c0 : i32
  } else {
    executor.print "no cuda devices"()
    scf.yield %c1 : i32
  }
  return %0 : i32
}

// CHECK: found {{[0-9]+}} cuda devices
// CHECK: start!
// CHECK: host_memref[0] = 1
// CHECK: host_memref[1] = 1
// CHECK: host_memref[2] = 1
// CHECK: host_memref[3] = 1
// CHECK: done!
