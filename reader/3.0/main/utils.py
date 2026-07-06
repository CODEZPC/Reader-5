"""
READER 3 - 工具模块
包含：资源包合并/解包、文件操作等底层工具函数。
"""

import glob
import logging
import os
import shutil
import struct
import tempfile


# ==================== BinUnpacker 类 ====================

class BinUnpacker:
    """二进制资源包解包器，支持分卷合并与解包输出。"""

    def __init__(self, bin_prefix, output_dir="extracted"):
        self.bin_prefix = bin_prefix
        self.output_dir = output_dir
        self.merged_file = f"{bin_prefix}_merged.bin"

    def merge_chunks(self):
        """合并分卷文件"""
        chunk_files = sorted(glob.glob(f"{self.bin_prefix}*"))
        if not chunk_files:
            raise FileNotFoundError(
                f"No files found with prefix '{self.bin_prefix}'"
            )

        logging.info(f"找到 {len(chunk_files)} 个分卷文件，开始合并...")

        with open(self.merged_file, "wb") as merged:
            for chunk in chunk_files:
                logging.info(f"处理分卷: {chunk}")
                with open(chunk, "rb") as f:
                    shutil.copyfileobj(f, merged)

        logging.info(f"合并完成: {self.merged_file}")
        return self.merged_file

    def unpack(self, bin_file=None):
        """解包二进制文件到输出目录"""
        bin_file = bin_file or self.merged_file

        if not os.path.exists(bin_file):
            raise FileNotFoundError(f"文件不存在: {bin_file}")

        os.makedirs(self.output_dir, exist_ok=True)
        logging.info(f"开始解包: {bin_file} -> {self.output_dir}")

        with open(bin_file, "rb") as f:
            file_count = struct.unpack("I", f.read(4))[0]
            logging.info(f"包含 {file_count} 个文件")

            for i in range(file_count):
                path_len = struct.unpack("I", f.read(4))[0]
                rel_path = f.read(path_len).decode("utf-8")
                file_size = struct.unpack("I", f.read(4))[0]
                file_data = f.read(file_size)

                full_path = os.path.join(self.output_dir, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                with open(full_path, "wb") as out_file:
                    out_file.write(file_data)

                logging.info(f"解包: {rel_path} ({file_size} 字节)")

        logging.info(f"解包完成! 共解压 {file_count} 个文件到 {self.output_dir}")

    def cleanup(self):
        """清理合并产生的临时文件"""
        if os.path.exists(self.merged_file):
            os.remove(self.merged_file)
            logging.info(f"已清理临时文件: {self.merged_file}")


# ==================== 便捷函数 ====================

def merge_and_unpack(prefix: str = ".\\pack\\resources.bin", output_file: str = None):
    """
    合并分卷文件并执行解包操作（返回字典，可选输出为 bin）

    :param prefix: 分卷文件前缀（默认 resources.bin）
    :param output_file: 可选，指定合并后的文件路径，应为 bin 后缀
    :return: 解包后的字典 {路径: 内容}，失败返回 -1
    """
    logging.info(f"搜索分卷文件: {prefix}*")
    parts = sorted(
        glob.glob(f"{prefix}[0-9][0-9][0-9]"),
        key=lambda x: int(x[-3:]),
    )

    if not parts:
        logging.error("未找到资源包")
        return -1

    logging.info(f"找到 {len(parts)} 个分卷文件，开始合并...")
    delete_temp = False
    if not output_file:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
        output_file = temp_file.name
        temp_file.close()
        delete_temp = True

    try:
        with open(output_file, "wb") as out_f:
            for part in parts:
                with open(part, "rb") as in_f:
                    while chunk := in_f.read(8192):
                        out_f.write(chunk)
        logging.info(f"分卷合并完成，开始解包解析...")
        return _unpack_to_dict(output_file)
    finally:
        if delete_temp and os.path.exists(output_file):
            os.unlink(output_file)


def _unpack_to_dict(input_bin):
    """
    将二进制包文件解包为字典（不写磁盘）

    :param input_bin: 包文件路径
    :return: dict {相对路径: 二进制内容}
    """
    result_dict = {}
    with open(input_bin, "rb") as bin_file:
        try:
            file_count = struct.unpack("I", bin_file.read(4))[0]
            logging.debug(f"资源包包含 {file_count} 个文件条目")
            for _ in range(file_count):
                path_len = struct.unpack("I", bin_file.read(4))[0]
                rel_path = bin_file.read(path_len).decode("utf-8-sig")
                file_size = struct.unpack("I", bin_file.read(4))[0]
                file_data = bin_file.read(file_size)
                result_dict[rel_path] = file_data
        except struct.error as e:
            logging.error(f"解析二进制文件时出错: {str(e)}")
            logging.error("文件可能已损坏或格式不正确")
        except Exception as e:
            logging.error(f"读取文件时出错: {str(e)}")
    logging.info(f"解压完成，共 {len(result_dict)} 个文件")
    return result_dict


def unpack_resources(
    bin_prefix=".\\pack\\resources.bin",
    output_dir="extracted",
    keep_temp=False,
):
    """
    解包资源并输出到磁盘目录。

    :param bin_prefix: 资源包前缀（默认 resources.bin）
    :param output_dir: 输出目录（默认 extracted）
    :param keep_temp: 是否保留临时文件（默认 False）
    """
    logging.info(f"解包资源包: {bin_prefix} -> {output_dir}")
    unpacker = BinUnpacker(bin_prefix, output_dir)
    try:
        if glob.glob(f"{bin_prefix}*") and not os.path.exists(bin_prefix):
            unpacker.merge_chunks()
            unpacker.unpack()
        else:
            unpacker.unpack(bin_prefix)
        if not keep_temp:
            unpacker.cleanup()
        logging.info(f"资源包解包完成: {output_dir}")
    except Exception as e:
        logging.error(f"解包输出错误: {e}")
        if not keep_temp:
            unpacker.cleanup()
