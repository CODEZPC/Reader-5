import os
import struct
import glob
import shutil

class BinUnpacker:
    def __init__(self, bin_prefix, output_dir='extracted'):
        self.bin_prefix = bin_prefix
        self.output_dir = output_dir
        self.merged_file = f"{bin_prefix}_merged.bin"
    
    def merge_chunks(self):
        """合并分卷文件"""
        chunk_files = sorted(glob.glob(f"{self.bin_prefix}*"))
        if not chunk_files:
            raise FileNotFoundError(f"No files found with prefix '{self.bin_prefix}'")
        
        print(f"找到 {len(chunk_files)} 个分卷文件，开始合并...")
        
        with open(self.merged_file, 'wb') as merged:
            for chunk in chunk_files:
                print(f"处理分卷: {chunk}")
                with open(chunk, 'rb') as f:
                    shutil.copyfileobj(f, merged)
        
        print(f"合并完成: {self.merged_file}")
        return self.merged_file
    
    def unpack(self, bin_file=None):
        """解包二进制文件"""
        bin_file = bin_file or self.merged_file
        
        if not os.path.exists(bin_file):
            raise FileNotFoundError(f"文件不存在: {bin_file}")
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"开始解包: {bin_file} -> {self.output_dir}")
        
        with open(bin_file, 'rb') as f:
            # 读取文件数量
            file_count = struct.unpack('I', f.read(4))[0]
            print(f"包含 {file_count} 个文件")
            
            for i in range(file_count):
                # 读取路径长度和路径
                path_len = struct.unpack('I', f.read(4))[0]
                rel_path = f.read(path_len).decode('utf-8')
                
                # 读取文件大小和内容
                file_size = struct.unpack('I', f.read(4))[0]
                file_data = f.read(file_size)
                
                # 创建目标路径
                full_path = os.path.join(self.output_dir, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # 写入文件
                with open(full_path, 'wb') as out_file:
                    out_file.write(file_data)
                
                print(f"解包: {rel_path} ({file_size} 字节)")
        
        print(f"解包完成! 共解压 {file_count} 个文件到 {self.output_dir}")
    
    def cleanup(self):
        """清理合并的临时文件"""
        if os.path.exists(self.merged_file):
            os.remove(self.merged_file)
            print(f"已清理临时文件: {self.merged_file}")

def unpack_resources(bin_prefix='resources.bin', output_dir='extracted', keep_temp=False):
    """直接解包resources.binxxx文件
    
    Args:
        bin_prefix (str): 分卷文件前缀 (如 "resources.bin")
        output_dir (str): 输出目录 (默认: extracted)
        keep_temp (bool): 是否保留合并后的临时文件
    """
    unpacker = BinUnpacker(bin_prefix, output_dir)
    
    try:
        # 判断是否是分卷文件
        if glob.glob(f"{bin_prefix}*") and not os.path.exists(bin_prefix):
            unpacker.merge_chunks()
            unpacker.unpack()
        else:
            # 如果是单个文件直接解包
            unpacker.unpack(bin_prefix)
        
        if not keep_temp:
            unpacker.cleanup()
    
    except Exception as e:
        print(f"错误: {e}")
        if not keep_temp:
            unpacker.cleanup()
