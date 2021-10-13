# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/04_util.ipynb (unless otherwise specified).

__all__ = ['sparse_to_dense_datacube_kernel_crop', 'sparse_to_dense_datacube_crop']

# Cell
from numba import cuda
@cuda.jit
def sparse_to_dense_datacube_kernel_crop(dc, frames, frame_dimensions, bin, start, end):
    ny, nx = cuda.grid(2)
    NY, NX, MYBIN, MXBIN = dc.shape
    MY, MX = frame_dimensions
    if ny < NY and nx < NX:
        for i in range(frames[ny, nx].shape[0]):
            idx1d = frames[ny, nx, i]
            my = idx1d // MX
            mx = idx1d - my * MX
            if my >= start[0] and mx >= start[1] and my < end[0] and mx < end[1]:
                mybin = (my - start[0]) // bin
                mxbin = (mx - start[1]) // bin
                if (mxbin >= 0 and mybin >= 0) and not (mxbin == 0 and mybin == 0):
                    # print(mybin, mxbin)
                    cuda.atomic.add(dc, (ny, nx, mybin, mxbin), 1)

# Cell
import numpy as np
import cupy as cp
def sparse_to_dense_datacube_crop(frames, scan_dimensions, frame_dimensions, center, radius, bin=1):
    radius = int(np.ceil(radius / bin) * bin)
    start = center - radius
    end = center + radius
    frame_size = 2 * radius // bin
    print(start,end)

    xp = cp.get_array_module(frames)
    dc = cp.zeros((*scan_dimensions, frame_size, frame_size), dtype=frames.dtype)

    threadsperblock = (16, 16)
    blockspergrid = tuple(np.ceil(np.array(frames.shape[:2]) / threadsperblock).astype(np.int))

    sparse_to_dense_datacube_kernel_crop[blockspergrid, threadsperblock](dc, frames, cp.array(frame_dimensions), bin,
                                                                         start, end)
    return dc