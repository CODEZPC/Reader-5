import os
import struct

def pack(source_folder, output_bin):
    file_list = []
    # 收集所有文件路径（相对路径）
    for root, _, files in os.walk(source_folder):
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, source_folder)
            file_list.append((rel_path, abs_path))
    
    with open(output_bin, 'wb') as bin_file:
        # 写入文件数量（4字节整数）
        bin_file.write(struct.pack('I', len(file_list)))
        
        for rel_path, abs_path in file_list:
            # 读取文件内容
            with open(abs_path, 'rb') as f:
                file_data = f.read()
            
            # 编码路径为UTF-8
            encoded_path = rel_path.encode('utf-8')
            
            # 写入路径长度（4字节）和路径内容
            bin_file.write(struct.pack('I', len(encoded_path)))
            bin_file.write(encoded_path)
            
            # 写入文件大小（4字节）和文件内容
            bin_file.write(struct.pack('I', len(file_data)))
            bin_file.write(file_data)

pack('resources', 'resources.bin')