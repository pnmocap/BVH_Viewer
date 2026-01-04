# BVH Viewer 打包脚本
# 自动执行打包流程并进行基本检查

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BVH Viewer 打包工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Python 环境
Write-Host "[1/6] 检查 Python 环境..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 未找到 Python。请确保 Python 3.8+ 已安装并添加到 PATH。" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python 环境: $pythonVersion" -ForegroundColor Green
Write-Host ""

# 2. 检查并安装依赖
Write-Host "[2/6] 检查依赖库..." -ForegroundColor Yellow
$requirements = @(
    "pygame>=2.5.2",
    "PyOpenGL==3.1.7",
    "numpy>=1.26.0",
    "pyinstaller>=5.13",
    "matplotlib"
)

Write-Host "安装/更新依赖库..." -ForegroundColor Cyan
pip install -r requirements.txt --upgrade
if ($LASTEXITCODE -ne 0) {
    Write-Host "警告: 依赖安装可能存在问题，但继续打包..." -ForegroundColor Yellow
}
Write-Host "✓ 依赖检查完成" -ForegroundColor Green
Write-Host ""

# 3. 清理之前的构建
Write-Host "[3/6] 清理旧的构建文件..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "✓ 已删除 build/ 目录" -ForegroundColor Green
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "✓ 已删除 dist/ 目录" -ForegroundColor Green
}
Write-Host ""

# 4. 检查必要文件
Write-Host "[4/6] 检查必要文件..." -ForegroundColor Yellow
$requiredFiles = @(
    "bvh_visualizer_improved.py",
    "build_bvh_viewer.spec",
    "app_icon.ico",
    "ui\__init__.py",
    "ui\components.py",
    "ui\renderer.py",
    "ui\colors.py",
    "ui\metrics.py"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
        Write-Host "✗ 缺少文件: $file" -ForegroundColor Red
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "错误: 缺少必要文件，无法继续打包。" -ForegroundColor Red
    exit 1
}
Write-Host "✓ 所有必要文件存在" -ForegroundColor Green
Write-Host ""

# 5. 开始打包
Write-Host "[5/6] 开始打包..." -ForegroundColor Yellow
Write-Host "这可能需要 3-5 分钟，请耐心等待..." -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date
pyinstaller build_bvh_viewer.spec --clean --noconfirm
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 打包失败!" -ForegroundColor Red
    Write-Host "请查看上方错误信息，或尝试手动运行: pyinstaller build_bvh_viewer.spec" -ForegroundColor Yellow
    exit 1
}
Write-Host ""
Write-Host "✓ 打包完成 (耗时: $([math]::Round($duration, 1)) 秒)" -ForegroundColor Green
Write-Host ""

# 6. 验证输出
Write-Host "[6/6] 验证输出文件..." -ForegroundColor Yellow
if (Test-Path "dist\BVH_Viewer.exe") {
    $fileSize = (Get-Item "dist\BVH_Viewer.exe").Length / 1MB
    Write-Host "✓ 可执行文件已生成: dist\BVH_Viewer.exe" -ForegroundColor Green
    Write-Host "  文件大小: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Cyan
    Write-Host ""
    
    # 显示配置文件位置提示
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  打包成功!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "可执行文件位置:" -ForegroundColor Cyan
    Write-Host "  $(Resolve-Path 'dist\BVH_Viewer.exe')" -ForegroundColor White
    Write-Host ""
    Write-Host "用户配置文件将保存到:" -ForegroundColor Cyan
    Write-Host "  $env:APPDATA\BVH_Viewer\bvh_viewer_config.json" -ForegroundColor White
    Write-Host ""
    Write-Host "下一步:" -ForegroundColor Cyan
    Write-Host "  1. 双击 dist\BVH_Viewer.exe 运行程序" -ForegroundColor White
    Write-Host "  2. 首次运行会自动创建配置文件" -ForegroundColor White
    Write-Host "  3. 可将整个 dist 目录打包分发给用户" -ForegroundColor White
    Write-Host ""
    Write-Host "提示: 如需调试，可使用 console=True 重新打包以查看输出" -ForegroundColor Yellow
    Write-Host ""
    
} else {
    Write-Host "错误: 未找到生成的可执行文件!" -ForegroundColor Red
    Write-Host "请检查打包过程中的错误信息。" -ForegroundColor Yellow
    exit 1
}
