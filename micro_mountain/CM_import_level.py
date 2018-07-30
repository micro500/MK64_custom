import math
import struct
import micro_mountain_config 

course_id = 1

with open("Mario Kart 64 (U) [!].z64",'rb') as rom_file:
  rom_data = rom_file.read()

level_data_rom_addr = 0x122390
path_addr_table_rom_addr = 0xDD4D0
path_len_table_rom_addr = 0xDE5D0
  
def mem_read_u32_be(addr, data):
  return struct.unpack(">I",data[addr:addr+4])[0]
  
def mem_read_u16_be(addr, data):
  return struct.unpack(">H",data[addr:addr+2])[0]
  
def u16_to_le(data):
    return struct.pack("<H",data)

def u16_to_be(data):
    return struct.pack(">H",data)

def s16_to_be(data):
    return struct.pack(">h",data)

def u32_to_be(data):
    return struct.pack(">I",data)
  
def mem_fill(data, start_addr, end_addr, value):
  return data[0:start_addr] + (bytes([value] * (end_addr - start_addr))) + data[end_addr:len(data)]
  
def mem_write_u32_be(addr, value, data):
  return data[0:addr] + u32_to_be(value) + data[(addr+4):len(data)]

def mem_write_u16_be(addr, value, data):
  return data[0:addr] + u16_to_be(value) + data[(addr+2):len(data)]
  
def mem_write_u8_be(addr, value, data):
  return data[0:addr] + u8_to_be(value) + data[(addr+1):len(data)]

def mem_write_16(addr, value, data):
  return data[0:addr] + value + data[(addr+2):len(data)]
  
def mio0_decode(input_data):
  if (input_data[0:4] != b"MIO0"):
    print("Error: MIO0 header missing")
    
  raw_size = mem_read_u32_be(4, input_data)
  comp_offset = mem_read_u32_be(8, input_data)
  raw_offset = mem_read_u32_be(12, input_data)
  
  map_offset = 0x10
  map_mask = 0x80
  
  output_data = b""
  
  # mio0_header *header = (mio0_header*)input;
  # uint8_t *output = (uint8_t*)malloc(header->rawSize);

  # uint32_t nBytesOutput = 0;
  # uint32_t compOffs     = header->compOffs;
  # uint32_t rawOffs      = header->rawOffs;
  # uint32_t mapOffs      = 0x10;
  # uint8_t  mapMask      = 0x80;
  # uint32_t outOffs      = 0;

  
  while (len(output_data) < raw_size):
    raw_flag = input_data[map_offset] & map_mask
    if (raw_flag):
      # copy one byte from raw data to output
      output_data = output_data + bytes([input_data[raw_offset]])
      raw_offset += 1
      
    else:
      # read 2 bytes from compOffs
      comp = mem_read_u16_be(comp_offset, input_data)
      comp_offset += 2
      byte_len = (comp >> 12) + 3
      offset = (comp & 0x0FFF) + 1

      # copy byte_len bytes from `output[outOffs - offs]` to output
      while (byte_len > 0 and len(output_data) < raw_size):
        output_data = output_data + bytes([output_data[len(output_data) - offset]])
        
        #offset += 1
        byte_len -= 1

    map_mask >>= 1;
    if(map_mask == 0):
      map_offset += 1
      map_mask = 0x80
      
  return output_data

def fake_MIO0_encode(data):
  output_data = b"MIO0"
  data_len = len(data)
  
  # Raw size
  output_data += u32_to_be(data_len)
  
  # Comp offset = 0 (no compressed data)
  output_data += bytes([0x00] * 4)

  # calculate number of layout bits needed
  layout_bits_len = int(math.ceil(data_len / 8))
  
  # Pad to a multiple of 16
  if ((layout_bits_len % 16) > 0):
    layout_bits_len += 16 - (layout_bits_len % 16)
  
  # Calculate final position of decomp bits
  decomp_offset = layout_bits_len + 16
  # Insert offset value
  output_data += u32_to_be(decomp_offset)
  
  # Insert layout bits
  output_data += bytes([0xFF] * layout_bits_len)
  # Insert data
  output_data += data
  
  return output_data

# Ported from https://github.com/queueRAM/sm64tools/blob/master/n64cksum.c
# by dkosmari https://gist.github.com/dkosmari/ee7bb471ea12c21b008d0ecffebd6384
def fix_checksum(buf):
    #local t0, t1, t2, t3, t4, t5, t6, t7, t8, t9
    #local s0, s6
    #local a0, a1, a2, a3, at
    #local lo
    #local v0, v1
    #local ra
    
    mask32 = 0xFFFFFFFF

    # derived from the SM64 boot code
    s6 = 0x3f
    a0 = 0x1000                     # 59c:   8d640008    lw a0,8(t3)
    a1 = s6                         # 5a0:   02c02825    move  a1,s6
    at = 0x5d588b65                 # 5a4:   3c015d58    lui   at,0x5d58
                                    # 5a8:   34218b65    ori   at,at,0x8b65
    lo = (a1 * at) & mask32         # 5ac:   00a10019    multu a1,at    16 F8CA 4DDB

    ra = 0x100000                   # 5bc:  3c1f0010    lui   ra,0x10
    v1 = 0                          # 5c0:  00001825    move  v1,zero
    t0 = 0                          # 5c4:  00004025    move  t0,zero
    t1 = a0                         # 5c8:  00804825    move  t1,a0
    t5 = 32                         # 5cc:  240d0020    li t5,32
    v0 = lo                         # 5d0:  00001012    mflo  v0
    v0 = (v0 + 1) & mask32          # 5d4:  24420001    addiu v0,v0,1
    a3 = v0                         # 5d8:  00403825    move  a3,v0
    t2 = v0                         # 5dc:  00405025    move  t2,v0
    t3 = v0                         # 5e0:  00405825    move  t3,v0
    s0 = v0                         # 5e4:  00408025    move  s0,v0
    a2 = v0                         # 5e8:  00403025    move  a2,v0
    t4 = v0                         # 5ec:  00406025    move  t4,v0

    while t0 != ra:
        v0 = mem_read_u32_be(t1, buf)   # 5f0: 8d220000    lw v0,0(t1)
        v1 = (a3 + v0) & mask32     # 5f4: 00e21821    addu  v1,a3,v0
        at = v1 < a3                # 5f8: 0067082b    sltu  at,v1,a3
        a1 = v1                     # 600: 00602825    move  a1,v1 branch delay slot
        if at:                      # 5fc: 10200002    beqz  at,0x608
            t2 = (t2 + 1) & mask32  # 604: 254a0001    addiu t2,t2,1

        v1 = v0 & 0x1F              # 608: 3043001f    andi  v1,v0,0x1f
        t7 = (t5 - v1) & mask32     # 60c: 01a37823    subu  t7,t5,v1
        t8 = v0 >> t7               # 610: 01e2c006    srlv  t8,v0,t7
        t6 = (v0 << v1) & mask32    # 614: 00627004    sllv  t6,v0,v1
        a0 = t6 | t8                # 618: 01d82025    or a0,t6,t8
        at = a2 < v0                # 61c: 00c2082b    sltu  at,a2,v0
        a3 = a1                     # 620: 00a03825    move  a3,a1
        t3 = (t3 ^ v0) & mask32     # 624: 01625826    xor   t3,t3,v0
        s0 = (s0 + a0) & mask32     # 62c: 02048021    addu  s0,s0,a0 branch delay slot
        if at:                      # 628: 10200004    beqz  at,0x63c
            t9 = (a3 ^ v0) & mask32 # 630: 00e2c826    xor   t9,a3,v0
                                    # 634: 10000002    b  0x640
            a2 = (a2 ^ t9) & mask32 # 638: 03263026    xor   a2,t9,a2 branch delay
        else:
            a2 = (a2 ^ a0) & mask32 # 63c: 00c43026    xor   a2,a2,a0

        t0 += 4                     # 640: 25080004    addiu t0,t0,4
        t7 = (v0 ^ s0) & mask32     # 644: 00507826    xor   t7,v0,s0
        t1 += 4                     # 648: 25290004    addiu t1,t1,4
        t4 = (t4 + t7) & mask32     # 650: 01ec6021    addu  t4,t7,t4 branch delay
                                    # 64c: 151fffe8    bne   t0,ra,0x5f0

    t6 = (a3 ^ t2) & mask32         # 654: 00ea7026    xor   t6,a3,t2
    a3 = (t6 ^ t3) & mask32         # 658: 01cb3826    xor   a3,t6,t3
    t8 = (s0 ^ a2) & mask32         # 65c: 0206c026    xor   t8,s0,a2
    s0 = (t8 ^ t4) & mask32         # 660: 030c8026    xor   s0,t8,t4
    
    buf = mem_write_u32_be(0x10, a3, buf)
    buf = mem_write_u32_be(0x14, s0, buf)
    
    return buf
  
# get seg6 addr in rom
seg6_mio0_rom_start_addr = mem_read_u32_be(level_data_rom_addr + (course_id * 48) + 0, rom_data)
seg6_mio0_rom_end_addr = mem_read_u32_be(level_data_rom_addr + (course_id * 48) + 4, rom_data)

# get seg6 block
# decode MIO0 
print("Decode seg6")
seg6_data = mio0_decode(rom_data[seg6_mio0_rom_start_addr:seg6_mio0_rom_end_addr])

# get seg9 addr in rom
seg9_mio0_rom_start_addr = mem_read_u32_be(level_data_rom_addr + (course_id * 48) + 16, rom_data)
seg9_mio0_rom_end_addr = mem_read_u32_be(level_data_rom_addr + (course_id * 48) + 20, rom_data)

# get seg9 block
seg9_data = rom_data[seg9_mio0_rom_start_addr:seg9_mio0_rom_end_addr]

# get seg47 addr in rom
seg47_rom_start_addr = mem_read_u32_be(level_data_rom_addr + (course_id * 48) + 8, rom_data)
seg47_rom_end_addr = mem_read_u32_be(level_data_rom_addr + (course_id * 48) + 12, rom_data)

# get seg47 block
seg47_data = rom_data[seg47_rom_start_addr:seg47_rom_end_addr]

seg4_data = mio0_decode(seg47_data)

seg47_ptr = mem_read_u32_be(level_data_rom_addr + (course_id * 48) + 24, rom_data)
seg7_ptr = mem_read_u32_be(level_data_rom_addr + (course_id * 48) + 32, rom_data)

seg7_offset = seg7_ptr - seg47_ptr
seg7_data = seg47_data[seg7_offset:]

new_rom_data = rom_data

# Disable checksum check
new_rom_data = mem_write_u32_be(0x688, 0, new_rom_data)

new_seg6_data = seg6_data

# overwrite the collision table
col_seg6_start_addr = 0x72D0
new_seg6_data = new_seg6_data[0:col_seg6_start_addr]
with open("micro_mountain_col.bin",'rb') as mm_col_file:
  mm_col_data = mm_col_file.read()
new_seg6_data += mm_col_data

with open("micro_mountain_path_data.bin",'rb') as mm_path_file:
  mm_path_data = mm_path_file.read()

# completely overwrite the path data
new_path_data = mm_path_data

new_path0_seg6_addr = 0x06000000 | len(new_seg6_data)
new_seg6_data += new_path_data
new_rom_data = mem_write_u32_be(path_addr_table_rom_addr + (course_id * 16) + 0, new_path0_seg6_addr, new_rom_data)

new_rom_data = mem_write_u16_be(0xDE5E0, int(len(new_path_data) / 8), new_rom_data)

for (list_id, item_box_list) in enumerate(micro_mountain_config.item_boxes):
  for i in range(0,5):
    new_seg6_data = mem_write_u16_be(0x7250 + list_id * (5*8) + i*8, item_box_list[i][0] & 0xFFFF, new_seg6_data)
    new_seg6_data = mem_write_u16_be(0x7250 + list_id * (5*8) + i*8 + 4, -item_box_list[i][1] & 0xFFFF, new_seg6_data)
    new_seg6_data = mem_write_u16_be(0x7250 + list_id * (5*8) + i*8 + 2, item_box_list[i][2] & 0xFFFF, new_seg6_data)    

with open("micro_mountain_seg7.bin",'rb') as mm_seg7_file:
  mm_seg7_data = mm_seg7_file.read()
  
seg7_data = seg7_data[:-16]

# null out all old seg7
seg7_data = bytes([0x2A] * 0xB5D)
# add our new data
seg7_data = seg7_data + mm_seg7_data
# terminate this list
seg7_data = seg7_data + bytes([0xFF]) + bytes([0x00] * 32)

with open("test_seg7.bin",'wb') as outfile:
  outfile.write(seg7_data)


with open("micro_mountain_seg4.bin",'rb') as mm_seg4_file:
  mm_seg4_data = mm_seg4_file.read()

# completely overwrite the vertex table with our data
seg4_data = mm_seg4_data

with open("test_seg4.bin",'wb') as outfile:
  outfile.write(seg4_data)  
  

with open("micro_mountain_textures.bin",'rb') as mm_texture_file:
  mm_texture_data = mm_texture_file.read()

seg9_data = mm_texture_data
seg9_data += bytes([0] * (0x150 - len(seg9_data)))


# load binary image data
# mio0 encode it
# append it to the rom
# get addr in rom, fix to 0F format
# patch entry in seg9 data
for image in micro_mountain_config.custom_textures:
  with open(image[1],'rb') as custom_img_file:
    custom_img_data = custom_img_file.read()
  custom_img_MIO0_data = fake_MIO0_encode(custom_img_data)
  
  custom_img_start_addr = len(new_rom_data)
  new_rom_data = new_rom_data + custom_img_MIO0_data
  
  custom_img_0F_addr = ((custom_img_start_addr - 0x641F70) & 0x00FFFFFF) | 0x0F000000
  
  seg9_data = mem_write_u32_be(image[0] * 16, custom_img_0F_addr, seg9_data)
  seg9_data = mem_write_u32_be(image[0] * 16 + 4, len(custom_img_MIO0_data), seg9_data)
  
  
with open("micro_mountain_secdir.bin",'rb') as mm_secdir_file:
  mm_secdir_data = mm_secdir_file.read()
seg9_data += mm_secdir_data

with open("test_seg9.bin",'wb') as outfile:
  outfile.write(seg9_data)
  
with open("test_seg6.bin",'wb') as outfile:
  outfile.write(new_seg6_data)
  
# fake MIO0 encode seg6
seg6_new_MIO0_data = fake_MIO0_encode(new_seg6_data)

new_seg6_start_addr = len(new_rom_data)
# Pad rom to a multiple of 16
if ((new_seg6_start_addr % 16) > 0):
  padding_len = 16 - (new_seg6_start_addr % 16)
  new_rom_data += "\xFF" * padding_len
  
  new_seg6_start_addr = len(new_rom_data)

new_seg6_end_addr = new_seg6_start_addr + len(seg6_new_MIO0_data)

# append seg6 to end of rom
new_rom_data = new_rom_data + seg6_new_MIO0_data

# update pointers
new_rom_data = mem_write_u32_be(level_data_rom_addr + (course_id * 48) + 0, new_seg6_start_addr, new_rom_data)
new_rom_data = mem_write_u32_be(level_data_rom_addr + (course_id * 48) + 4, new_seg6_end_addr, new_rom_data)

# overwrite old seg6 with 00
new_rom_data = mem_fill(new_rom_data, seg6_mio0_rom_start_addr, seg6_mio0_rom_end_addr, 0xFF)

# append seg9 to end of rom
new_seg9_start_addr = len(new_rom_data)
# Pad rom to a multiple of 16
if ((new_seg9_start_addr % 16) > 0):
  padding_len = 16 - (new_seg9_start_addr % 16)
  new_rom_data += bytes([0xFF] * padding_len)
  
  new_seg9_start_addr = len(new_rom_data)

new_seg9_end_addr = new_seg9_start_addr + len(seg9_data)

new_rom_data = new_rom_data + seg9_data

# update pointers
new_rom_data = mem_write_u32_be(level_data_rom_addr + (course_id * 48) + 16, new_seg9_start_addr, new_rom_data)
new_rom_data = mem_write_u32_be(level_data_rom_addr + (course_id * 48) + 20, new_seg9_end_addr, new_rom_data)

# overwrite old seg9 with 00
new_rom_data = mem_fill(new_rom_data, seg9_mio0_rom_start_addr, seg9_mio0_rom_end_addr, 0xFF)

# fake MIO0 encode seg6
seg4_new_MIO0_data = fake_MIO0_encode(seg4_data)

# append seg47 to end of rom
new_seg47_start_addr = len(new_rom_data)
# Pad rom to a multiple of 16
if ((new_seg47_start_addr % 16) > 0):
  padding_len = 16 - (new_seg47_start_addr % 16)
  new_rom_data += bytes([0xFF] * padding_len)
  
  new_seg47_start_addr = len(new_rom_data)

new_seg47_end_addr = new_seg47_start_addr + len(seg4_new_MIO0_data) + len(seg7_data)

new_rom_data = new_rom_data + seg4_new_MIO0_data + seg7_data

# update pointers
new_rom_data = mem_write_u32_be(level_data_rom_addr + (course_id * 48) + 8, new_seg47_start_addr, new_rom_data)
new_rom_data = mem_write_u32_be(level_data_rom_addr + (course_id * 48) + 12, new_seg47_end_addr, new_rom_data)

new_rom_data = mem_write_u32_be(level_data_rom_addr + (course_id * 48) + 32, 0x0F000000 + len(seg4_new_MIO0_data), new_rom_data)

# overwrite old seg47 with 00
new_rom_data = mem_fill(new_rom_data, seg47_rom_start_addr, seg47_rom_end_addr, 0xFF)

seg7_len = mem_read_u32_be(level_data_rom_addr + (course_id * 48) + 36, rom_data)
#seg7_len += 0x5D40
seg7_len = micro_mountain_config.seg7_final_addr
new_rom_data = mem_write_u32_be(level_data_rom_addr + (course_id * 48) + 36, seg7_len, new_rom_data)

# update number of vertices
new_rom_data = mem_write_u32_be(level_data_rom_addr + (course_id * 48) + 28, int(len(seg4_data) / 14), new_rom_data)

#update "railings" dlist address
transparency_double_list = 0x07000000 | micro_mountain_config.transparency_double_list

new_rom_data = mem_write_u16_be(0xFC2DE, (transparency_double_list >> 16) & 0xFFFF, new_rom_data)
new_rom_data = mem_write_u16_be(0xFC2E2, transparency_double_list & 0xFFFF, new_rom_data)


transparency_single_list = 0x07000000 | micro_mountain_config.transparency_single_list

new_rom_data = mem_write_u16_be(0xFC31A, (transparency_single_list >> 16) & 0xFFFF, new_rom_data)
new_rom_data = mem_write_u16_be(0xFC332, transparency_single_list & 0xFFFF, new_rom_data)

# set up flowing lava
# override BB's level update code
new_rom_data = mem_write_u16_be(0xFFCBE, 1, new_rom_data)

# store the flowing lava dlist address
flowing_lava_list = 0x07000000 | micro_mountain_config.flowing_lava_list
flowing_lava_list_high = (flowing_lava_list >> 16) & 0xFFFF
flowing_lava_list_low = flowing_lava_list & 0xFFFF

if (flowing_lava_list_low >= 0x8000):
  flowing_lava_list_high = flowing_lava_list_high + 1
  
new_rom_data = mem_write_u16_be(0xFFEA2, flowing_lava_list_high, new_rom_data)
new_rom_data = mem_write_u16_be(0xFFEA6, flowing_lava_list_low, new_rom_data)


with open("micro_mountain_minimap.bin",'rb') as mm_minimap_file:
  mm_minimap_data = mm_minimap_file.read()

minimap_new_MIO0_data = fake_MIO0_encode(mm_minimap_data)
new_minimap_start_addr = len(new_rom_data)
if ((new_minimap_start_addr % 16) > 0):
  padding_len = 16 - (new_minimap_start_addr % 16)
  new_rom_data += bytes([0xFF] * padding_len)
  
  new_minimap_start_addr = len(new_rom_data)

new_rom_data = new_rom_data + minimap_new_MIO0_data

new_minimap_table_addr = (new_minimap_start_addr - 0x641F70) | 0x0F000000
new_rom_data = mem_write_u32_be(0xE60D0 + (course_id * 4), new_minimap_table_addr, new_rom_data)


# update length of minimap data
new_rom_data = mem_write_u16_be(0xE6120 + (course_id * 2), len(minimap_new_MIO0_data), new_rom_data)

# update minimap scale
new_rom_data = mem_write_u32_be(0xEF5A0 + (course_id * 4), 0x3c9fbe77, new_rom_data)

# update minimap offset x
new_rom_data = mem_write_u16_be(0x6FD92, 0x33, new_rom_data)

# update minimap offset y
new_rom_data = mem_write_u16_be(0x6FDA2, 0x0B, new_rom_data)

new_rom_data = fix_checksum(new_rom_data)

with open("MK64_Micro_Mountain.z64",'wb') as outfile:
  outfile.write(new_rom_data)
  
