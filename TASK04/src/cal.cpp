#include <iostream>
#include <windows.h>
#include <xmmintrin.h>
#include <immintrin.h>


// 计时结构
LARGE_INTEGER t1, t2, tc;

void time_begin()
{
	QueryPerformanceFrequency(&tc);
	QueryPerformanceCounter(&t1);
}

float time_end()
{
	QueryPerformanceCounter(&t2);
	return ((t2.QuadPart - t1.QuadPart)*1.0 / tc.QuadPart) * 1000;
}


class matrix4
{
public:
	matrix4()
		:data{ 0 }
	{

	}

	matrix4(float v)
		:data{ v,0,0,0,0,v,0,0,0,0,v,0,0,0,0,v }
	{

	}

public:

public:
	union
	{
		float data[16];
		float ptr[4][4];
	};
};

// 列主序按行计算
matrix4 mul_1(const matrix4& m1, const matrix4& m2)
{
	matrix4 ret;
	for (int row = 0; row < 4; ++row) 
	{
		for (int col = 0; col < 4; ++col) 
		{
			for (int a = 0; a < 4; ++a) 
			{
				ret.ptr[col][row] += m1.ptr[a][row] * m2.ptr[col][a];
			}
		}
	}

	return ret;
}

__declspec(align(16)) matrix4 A(1.f);
__declspec(align(16)) matrix4 B(2.f);
__declspec(align(16)) float v[16]
= {0, 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15};



__declspec(align(16)) __m256i gatherA12 = _mm256_set_epi32(13, 9, 5, 1, 12, 8, 4, 0);
__declspec(align(16)) __m256i gatherA34 = _mm256_set_epi32(15, 11, 7, 3, 14, 10, 6, 2);

__declspec(align(16)) __m256i gatherB11 = _mm256_set_epi32(3, 2, 1, 0, 3, 2, 1, 0);
__declspec(align(16)) __m256i gatherB22 = _mm256_set_epi32(7, 6, 5, 4, 7, 6, 5, 4);
__declspec(align(16)) __m256i gatherB33 = _mm256_set_epi32(11, 10, 9, 8, 11, 10, 9, 8);
__declspec(align(16)) __m256i gatherB44 = _mm256_set_epi32(15, 14, 13, 12, 15, 14, 13, 12);

auto mm_mul_mat(matrix4 const& _Left, matrix4 const& _Right)
{
	matrix4 ret;
	__declspec(align(16)) __m256 temp;
	__declspec(align(16)) __m256 a12, a34;
	__declspec(align(16)) __m256 b11, b22, b33, b44;
	a12 = _mm256_i32gather_ps(_Left.data, gatherA12, sizeof(float));
	a34 = _mm256_i32gather_ps(_Left.data, gatherA34, sizeof(float));

	b11 = _mm256_i32gather_ps(_Right.data, gatherB11, sizeof(float));
	b22 = _mm256_i32gather_ps(_Right.data, gatherB22, sizeof(float));
	b33 = _mm256_i32gather_ps(_Right.data, gatherB33, sizeof(float));
	b44 = _mm256_i32gather_ps(_Right.data, gatherB44, sizeof(float));

	temp = _mm256_dp_ps(a12, b11, 0b11110001);
	ret.data[0] = temp.m256_f32[0];
	ret.data[1] = temp.m256_f32[4];
	temp = _mm256_dp_ps(a34, b11, 0b11110001);
	ret.data[2] = temp.m256_f32[0];
	ret.data[3] = temp.m256_f32[4];

	temp = _mm256_dp_ps(a12, b22, 0b11110001);
	ret.data[4] = temp.m256_f32[0];
	ret.data[5] = temp.m256_f32[4];
	temp = _mm256_dp_ps(a34, b22, 0b11110001);
	ret.data[6] = temp.m256_f32[0];
	ret.data[7] = temp.m256_f32[4];

	temp = _mm256_dp_ps(a12, b33, 0b11110001);
	ret.data[8] = temp.m256_f32[0];
	ret.data[9] = temp.m256_f32[4];
	temp = _mm256_dp_ps(a34, b33, 0b11110001);
	ret.data[10] = temp.m256_f32[0];
	ret.data[11] = temp.m256_f32[4];

	temp = _mm256_dp_ps(a12, b44, 0b11110001);
	ret.data[12] = temp.m256_f32[0];
	ret.data[13] = temp.m256_f32[4];
	temp = _mm256_dp_ps(a34, b44, 0b11110001);
	ret.data[14] = temp.m256_f32[0];
	ret.data[15] = temp.m256_f32[4];

	return ret;
}

int main()
{

	time_begin();
	for (int i = 0; i < 10000000; ++i)
	{
		volatile auto res = mm_mul_mat(A, B);
	}
	::std::cout << "SIMD-AVX \ttime: " << time_end() << ::std::endl;

	time_begin();
	for (int i = 0; i < 10000000; ++i)
	{
		volatile auto m = mul_1(A, B);
	}
	::std::cout << "SISD TRIVIAL \ttime: " << time_end() << ::std::endl;



	return 0;
}
