# 保存为 split.ps1 文件并运行
param(
    [string]$Path = "resources.bin",
    [int64]$PartSizeBytes = 80MB,
    [string]$DestinationPath = ".\splited"
)

# 创建输出目录
New-Item -ItemType Directory -Force -Path $DestinationPath | Out-Null

# 计算需要多少分卷
$file = Get-Item $Path
$totalSize = $file.Length
$partCount = [Math]::Ceiling($totalSize / $PartSizeBytes)

# 开始拆分
$stream = [System.IO.File]::OpenRead($Path)
$buffer = New-Object byte[] $PartSizeBytes
$partNumber = 1

for ($i = 0; $i -lt $partCount; $i++) {
    # 读取分卷数据
    $bytesRead = $stream.Read($buffer, 0, $buffer.Length)
    
    # 生成分卷文件名
    $partName = "{0}\{1}.bin{2:D3}" -f $DestinationPath, $file.BaseName, $partNumber
    $partStream = [System.IO.File]::OpenWrite($partName)
    
    # 写入分卷文件
    $partStream.Write($buffer, 0, $bytesRead)
    $partStream.Close()
    
    Write-Host "File written: $partName"
    $partNumber++
}

$stream.Close()