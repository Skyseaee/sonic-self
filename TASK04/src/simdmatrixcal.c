#include <immintrin.h>

#include "naivematrixcal.h"
#include "simdmatrixcal.h"


/*
matrix = [[0,  1,   2,  3],
          [4,  5,   6,  7],
          [8,  9,  10, 11],
          [12, 13, 14, 15]]
*/
void matrix_multiply_simd_c(float *A, float *B, float *C) {
    __declspec(align(16)) __m256i gatherA12 = _mm256_set_epi32(13, 9, 5, 1, 12, 8, 4, 0);
    __declspec(align(16)) __m256i gatherA34 = _mm256_set_epi32(15, 11, 7, 3, 14, 10, 6, 2);

    __declspec(align(16)) __m256i gatherB11 = _mm256_set_epi32(3, 2, 1, 0, 3, 2, 1, 0);
    __declspec(align(16)) __m256i gatherB22 = _mm256_set_epi32(7, 6, 5, 4, 7, 6, 5, 4);
    __declspec(align(16)) __m256i gatherB33 = _mm256_set_epi32(11, 10, 9, 8, 11, 10, 9, 8);
    __declspec(align(16)) __m256i gatherB44 = _mm256_set_epi32(15, 14, 13, 12, 15, 14, 13, 12);

    __declspec(align(16)) __m256 temp;
	__declspec(align(16)) __m256 a12, a34;
	__declspec(align(16)) __m256 b11, b22, b33, b44;

    a12 = _mm256_i32gather_ps(A, gatherA12, sizeof(float));
	a34 = _mm256_i32gather_ps(A, gatherA34, sizeof(float));

	b11 = _mm256_i32gather_ps(B, gatherB11, sizeof(float));
	b22 = _mm256_i32gather_ps(B, gatherB22, sizeof(float));
	b33 = _mm256_i32gather_ps(B, gatherB33, sizeof(float));
	b44 = _mm256_i32gather_ps(B, gatherB44, sizeof(float));

    temp = _mm256_dp_ps(a12, b11, 0b11110001);
	C[1] = temp.m256_f32[4];
	C[0] = temp.m256_f32[0];
	temp = _mm256_dp_ps(a34, b11, 0b11110001);
	C[2] = temp.m256_f32[0];
	C[3] = temp.m256_f32[4];

	temp = _mm256_dp_ps(a12, b22, 0b11110001);
	C[4] = temp.m256_f32[0];
	C[5] = temp.m256_f32[4];
	temp = _mm256_dp_ps(a34, b22, 0b11110001);
	C[6] = temp.m256_f32[0];
	C[7] = temp.m256_f32[4];

	temp = _mm256_dp_ps(a12, b33, 0b11110001);
	C[8] = temp.m256_f32[0];
	C[9] = temp.m256_f32[4];
	temp = _mm256_dp_ps(a34, b33, 0b11110001);
	C[10] = temp.m256_f32[0];
	C[11] = temp.m256_f32[4];

	temp = _mm256_dp_ps(a12, b44, 0b11110001);
	C[12] = temp.m256_f32[0];
	C[13] = temp.m256_f32[4];
	temp = _mm256_dp_ps(a34, b44, 0b11110001);
	C[14] = temp.m256_f32[0];
	C[15] = temp.m256_f32[4];
}