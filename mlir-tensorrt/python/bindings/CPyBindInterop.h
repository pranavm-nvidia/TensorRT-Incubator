//===- CPyBindInterop.h -----------------------------------------*- C++ -*-===//
//
// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
//===----------------------------------------------------------------------===//
///
/// This file contains important definitions and macros for definining C API <->
/// Python Capsule conversion functions that are common to both the
/// `mlir_tensorrt.compiler` and `mlir_tensorrt.runtime` package PyBind modules.
///
//===----------------------------------------------------------------------===//
#ifndef BINDINGS_CPYBINDINTEROP
#define BINDINGS_CPYBINDINTEROP

#if !defined(_MSC_VER)
#include <Python.h>
#endif

#include "mlir-tensorrt-c/Compiler/Compiler.h"

#define MTRT_PYTHON_CAPI_PTR_ATTR "_CAPIPtr"

#define MTRT_PYTHON_COMPILER_API_NAMESPACE "mlir_tensorrt.compiler.api"
#define MTRT_PYTHON_RUNTIME_API_NAMESPACE "mlir_tensorrt.runtime.api"

#define MTRT_COMPILER_CAPI_PTR_PATH(x)                                         \
  MTRT_PYTHON_COMPILER_API_NAMESPACE "." #x "." MTRT_PYTHON_CAPI_PTR_ATTR

#define MTRT_RUNTIME_CAPI_PTR_PATH(x)                                          \
  MTRT_PYTHON_COMPILER_API_NAMESPACE "." #x "." MTRT_PYTHON_CAPI_PTR_ATTR

/// A utility macro that declares inline static functions
/// `mtrtPython[objName]ToCapsule` and `mtrtPythonCapsuleTo[objName]`. These can
/// be used to build adaptors for the appropriate Python integration framework
/// (e.g. we use the in Pybind11 type casters).
#define MTRT_DEFINE_COMPILER_INLINE_PY_CAPSULE_CASTER_FUNCS(objName)           \
  static inline PyObject *mtrtPython##objName##ToCapsule(                      \
      MTRT_##objName options) {                                                \
    return PyCapsule_New(options.ptr, MTRT_COMPILER_CAPI_PTR_PATH(objName),    \
                         NULL);                                                \
  }                                                                            \
  static inline MTRT_##objName mtrtPythonCapsuleTo##objName(                   \
      PyObject *capsule) {                                                     \
    void *ptr =                                                                \
        PyCapsule_GetPointer(capsule, MTRT_COMPILER_CAPI_PTR_PATH(objName));   \
    return MTRT_##objName{ptr};                                                \
  }

#define MTRT_DEFINE_RUNTIME_INLINE_PY_CAPSULE_CASTER_FUNCS(objName)            \
  static inline PyObject *mtrtPython##objName##ToCapsule(                      \
      MTRT_##objName options) {                                                \
    return PyCapsule_New(options.ptr, MTRT_RUNTIME_CAPI_PTR_PATH(objName),     \
                         NULL);                                                \
  }                                                                            \
  static inline MTRT_##objName mtrtPythonCapsuleTo##objName(                   \
      PyObject *capsule) {                                                     \
    void *ptr =                                                                \
        PyCapsule_GetPointer(capsule, MTRT_RUNTIME_CAPI_PTR_PATH(objName));    \
    return MTRT_##objName{ptr};                                                \
  }

#endif // BINDINGS_CPYBINDINTEROP
