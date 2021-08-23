#include <stdio.h>
#include <math.h>

const double bt709_coeff_r = 0.2126;
const double bt709_coeff_g = 0.7152;
const double bt709_coeff_b = 0.0722;
const double bt709_coeff_ri = 1.0-bt709_coeff_r;
const double bt709_coeff_bi = 1.0-bt709_coeff_b;
const double bt709_coeff_bg = bt709_coeff_b / bt709_coeff_g;
const double bt709_coeff_rg = bt709_coeff_r / bt709_coeff_g;

const int y_offset = 16 << 8;
const int y_range = 219;
const int cr_offset = 128 << 8;
const int cr_range = 224;
const int cr_middle = 224/2;

const double bt709_ri_range = bt709_coeff_ri / cr_middle;
const double bt709_bi_range = bt709_coeff_bi / cr_middle;

// RED   3a 96 64 fa   3a 9e fc fa
// GREEN 3a 92 9a b2   3a 91 a6 b2

//       AA AB BY YY   AA AR RY YY
//       12 bits of alpha
//       10 bits of Cb
//       10 bits of luma
//       12 bits of alpha
//       10 bits of Cr
//       10 bits of luma

int main() {
    freopen(NULL, "rb", stdin);
    //freopen(NULL, "wb", stdout);
    char buffer[8] = { 0 };
    char outbuffer[8] = { 0 };
    int pixel_size = 8;
    while (fread(buffer, pixel_size, 1, stdin)) {

        // Convert 10-bit BT.709 Y'CbCrA 4:2:2 to RGB
        // Unpack bytes to 2xY 2xA and a B and R pair
        unsigned short a1 = (buffer[0] << 4) + ((buffer[1] & 0xf0) >> 4);
        unsigned short a2 = (buffer[4] << 4) + ((buffer[5] & 0xf0) >> 4);
        unsigned short cb = ((buffer[1] & 0x0f) << 6) + ((buffer[2] & 0xfc) >> 2);
        unsigned short cr = ((buffer[5] & 0x0f) << 6) + ((buffer[6] & 0xfc) >> 2);
        unsigned short y1 = ((buffer[2] & 0x03) << 8) + (buffer[3] & 0xff);
        unsigned short y2 = ((buffer[6] & 0x03) << 8) + (buffer[7] & 0xff);

        float cbf = bt709_bi_range * ((cb<<6) - cr_offset);
        float crf = bt709_ri_range * ((cr<<6) - cr_offset);
        float y1f = ((double)(y1 << 6)-y_offset) / y_range;
        float y2f = ((double)(y2 << 6)-y_offset) / y_range;

        // printf("Y: %f Cr: %f Cb: %f\n", y1f, cbf, crf);

        float r1f = fmin(255, y1f + crf);
        float g1f = fmin(255, y1f - cbf * bt709_coeff_bg - crf * bt709_coeff_rg);
        float b1f = fmin(255, y1f + cbf);
        float r2f = fmin(255, y2f + crf);
        float g2f = fmin(255, y2f - cbf * bt709_coeff_bg - crf * bt709_coeff_rg);
        float b2f = fmin(255, y2f + cbf);

        //printf("R: %f G: %f B: %f\n", r1f, g1f, b1f);
        //return 1;

        outbuffer[0] = (unsigned char)r1f;
        outbuffer[1] = (unsigned char)g1f;
        outbuffer[2] = (unsigned char)b1f;
        outbuffer[3] = (unsigned char)(((double)(a1 -16)) / 3.6);
        outbuffer[4] = (unsigned char)r2f;
        outbuffer[5] = (unsigned char)g2f;
        outbuffer[6] = (unsigned char)b2f;
        outbuffer[7] = (unsigned char)(((double)(a2 -16)) / 3.6);
        fwrite(outbuffer, pixel_size, 1, stdout);
    }
    fclose(stdin);
    fclose(stdout);
}