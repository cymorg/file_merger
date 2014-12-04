#!/usr/bin/env python

# Calculate a CRC value to be used by CRC calculation functions.
CRC32_POLYNOMIAL = 0xEDB88320L
def CRC32Value(i):
    j = 0
    ulCRC = 0
    ulCRC = i
    for j in range(8,0,-1):
        if ulCRC & 1:
            ulCRC = ( ulCRC >> 1 ) ^ CRC32_POLYNOMIAL
        else:
            ulCRC >>= 1
    return ulCRC

# Calculates the CRC-32 of a block of data all at once
def CalculateBlockCRC32(ulCount, ucBuffer):
    bc = 0
    ulTemp1 = 0
    ulTemp2 = 0
    ulCRC = 0
    while ulCount != 0:
        ulCount -= 1
        ulTemp1 = ( ulCRC >> 8 ) & 0x00FFFFFFL
        ulTemp2 = CRC32Value((ulCRC ^ ucBuffer[bc]) & 0xff )
        #ucBuffer += 1
        bc += 1
        ulCRC = ulTemp1 ^ ulTemp2
    return ulCRC

def main():
    b_array = bytearray(b"lkj23,m4df098-v8cx 909f2jkl54kwm cv98cv90iujk341k3jekjfsc098ivujakdf98)(*UJHKNk3jklj234#4@#$@#4@3jsd09fv")
    print "CRC = %d\n" % (CalculateBlockCRC32(len(b_array), b_array))


if __name__ == "__main__":
    main()
