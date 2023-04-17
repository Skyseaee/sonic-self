#include "naivematrixcal.h"

// 4*4 matrix
void matrix_multiply_c(float *A, float *B, float *C) {
    for (int i_idx=0; i_idx < 4; i_idx++) {
        for (int j_idx=0; j_idx < 4; j_idx++) {
            C[n*j_idx + i_idx] = 0;
            for (int k_idx=0; k_idx < 4; k_idx++) {
                C[n*j_idx + i_idx] += A[n*k_idx + i_idx]*B[k*j_idx + k_idx];
            }
        }
    }
}


