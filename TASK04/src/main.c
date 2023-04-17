#include <stdio.h>
#include <time.h>
#include <xmmintrin.h>
#include <immintrin.h>

// 4*4 matrix
void matrix_multiply_c(float *A, float *B, float *C, int i) {
    for (int i_idx=0; i_idx < 4; i_idx++) {
        for (int j_idx=0; j_idx < 4; j_idx++) {
            C[4*j_idx + i_idx] = 0;
            for (int k_idx=0; k_idx < 4; k_idx++) {
                C[4*j_idx + i_idx] += A[4*k_idx + i_idx]*B[4*j_idx + k_idx];
            }
        }
    }
    if(i==1) {
        for(int j=0; j<16; j++) {
            printf("%f\t", C[j]);
        }
        printf("\n");
    }
}

/*
matrix = [[0,  1,   2,  3],
          [4,  5,   6,  7],
          [8,  9,  10, 11],
          [12, 13, 14, 15]]
*/
void matrix_multiply_simd_c(float *A, float *B, float *C, int i) {
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
    C[0] = _mm256_cvtss_f32(temp);
	C[1] = _mm256_cvtss_f32(temp);
    
	temp = _mm256_dp_ps(a34, b11, 0b11110001);
	C[2] = _mm256_cvtss_f32(temp);
	C[3] = _mm256_cvtss_f32(temp);

	temp = _mm256_dp_ps(a12, b22, 0b11110001);
	C[4] = _mm256_cvtss_f32(temp);
	C[5] = _mm256_cvtss_f32(temp);
	temp = _mm256_dp_ps(a34, b22, 0b11110001);
	C[6] = _mm256_cvtss_f32(temp);
	C[7] = _mm256_cvtss_f32(temp);

	temp = _mm256_dp_ps(a12, b33, 0b11110001);
	C[8] = _mm256_cvtss_f32(temp);
	C[9] = _mm256_cvtss_f32(temp);
	temp = _mm256_dp_ps(a34, b33, 0b11110001);
	C[10] = _mm256_cvtss_f32(temp);
	C[11] = _mm256_cvtss_f32(temp);

	temp = _mm256_dp_ps(a12, b44, 0b11110001);
	C[12] = _mm256_cvtss_f32(temp);
	C[13] = _mm256_cvtss_f32(temp);
	temp = _mm256_dp_ps(a34, b44, 0b11110001);
	C[14] = _mm256_cvtss_f32(temp);
	C[15] = _mm256_cvtss_f32(temp);

    if(i==1) {
        for(int j=0; j<16; j++) {
            printf("%f\t", C[j]);
        }
        printf("\n");
    }
}

int main() {
    clock_t start, finish, start1, finish1;
    double Total_time, Total_time1;

    float A[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15};
    float B[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15};
    float C[] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    start = clock();
    for(int i=0; i<1000000000; i++) {
        matrix_multiply_c(A, B, C, i);
    }
    finish = clock();
    Total_time = (double)(finish - start) / CLOCKS_PER_SEC;
    printf("%f seconds\n", Total_time);

    start1 = clock();
    for(int i=0; i<1000000000; i++) {
        matrix_multiply_simd_c(A, B, C, i);
    }
    finish1 = clock();
    Total_time1 = (double)(finish1 - start1) / CLOCKS_PER_SEC;
    printf("%f seconds\n", Total_time1);

    return 0;
}