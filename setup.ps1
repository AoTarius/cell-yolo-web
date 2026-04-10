# ==========================================
# Cell-Yolo 自动化安装脚本 (Windows)
# ==========================================
# 此脚本会自动执行 QUICK-START.md 中的步骤
# 在需要用户输入的地方会提示输入
#
# 使用方法：
#   1. 在 web 目录下运行: .\setup.ps1
#   2. 从其他位置运行: cd C:\path\to\project\web && .\setup.ps1
#   3. 使用绝对路径运行: C:\path\to\project\web\setup.ps1
#
# 注意：脚本必须位于项目的 web 目录下
# ==========================================

# 设置错误处理
$ErrorActionPreference = "Stop"

# 配置变量
$CONDA_ENV_NAME = "cell-yolo"
$PYTHON_VERSION = "3.11"
$DB_NAME = "cell_tracking"
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$BACKEND_DIR = Join-Path $PROJECT_ROOT "web\backend"
$FRONTEND_DIR = Join-Path $PROJECT_ROOT "web\frontend"

# ==========================================
# 工具函数
# ==========================================

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Print-Step {
    param([string]$Message)
    Write-ColorOutput ""
    Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
    Write-ColorOutput "  $Message" "Cyan"
    Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
    Write-ColorOutput ""
}

function Print-Success {
    param([string]$Message)
    Write-ColorOutput "✓ $Message" "Green"
}

function Print-Error {
    param([string]$Message)
    Write-ColorOutput "✗ $Message" "Red"
}

function Print-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠ $Message" "Yellow"
}

function Print-Info {
    param([string]$Message)
    Write-ColorOutput "ℹ $Message" "Cyan"
}

function Test-Command {
    param([string]$Command)
    try {
        $null = Get-Command $Command -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Test-Confirmation {
    param([string]$Message)
    $response = Read-Host "$Message (y/n)"
    return $response -eq 'y' -or $response -eq 'Y'
}

# ==========================================
# 环境检查
# ==========================================

function Check-Environment {
    Print-Step "1/7 检查系统环境"

    # 检查 conda
    if (Test-Command "conda") {
        Print-Success "已找到 conda"
    }
    else {
        Print-Error "未找到 conda，请先安装 Anaconda 或 Miniconda"
        Write-ColorOutput "下载地址: https://docs.conda.io/en/latest/miniconda.html" "White"
        exit 1
    }

    # 检查 MySQL
    if (Test-Command "mysql") {
        Print-Success "已找到 MySQL"
    }
    else {
        Print-Warning "未找到 MySQL"
        Write-ColorOutput "请手动安装 MySQL 后再运行此脚本" "Yellow"
        Write-ColorOutput "下载地址: https://dev.mysql.com/downloads/installer/" "White"
        Write-ColorOutput "选择 'Developer Default' 进行安装" "White"
        exit 1
    }

    # 检查 Node.js
    if (Test-Command "node") {
        $nodeVersion = node -v
        Print-Success "已找到 Node.js (版本: $nodeVersion)"
    }
    else {
        Print-Error "未找到 Node.js"
        Write-ColorOutput "请安装 Node.js ^20.19.0 或 >=22.12.0" "Yellow"
        Write-ColorOutput "下载地址: https://nodejs.org/" "White"
        exit 1
    }

    # 检查 npm
    if (Test-Command "npm") {
        Print-Success "已找到 npm"
    }
    else {
        Print-Error "未找到 npm"
        exit 1
    }

    Print-Success "环境检查完成"
}

# ==========================================
# 创建和激活 conda 环境
# ==========================================

function Setup-CondaEnv {
    Print-Step "2/7 设置 Python 虚拟环境"

    # 检查环境是否已存在
    $envList = conda env list
    if ($envList -match "^${CONDA_ENV_NAME}\s") {
        Print-Warning "Conda 环境 '$CONDA_ENV_NAME' 已存在"
        if (Test-Confirmation "是否删除并重新创建环境?") {
            conda env remove -n $CONDA_ENV_NAME -y
            Print-Info "正在创建 conda 环境..."
            conda create -n $CONDA_ENV_NAME python=$PYTHON_VERSION -y
            Print-Success "Conda 环境创建成功"
        }
        else {
            Print-Info "使用现有的 conda 环境"
        }
    }
    else {
        Print-Info "正在创建 conda 环境..."
        conda create -n $CONDA_ENV_NAME python=$PYTHON_VERSION -y
        Print-Success "Conda 环境创建成功"
    }

    # 激活环境
    Print-Info "激活 conda 环境..."
    conda activate $CONDA_ENV_NAME
    Print-Success "Conda 环境已激活"
}

# ==========================================
# 配置环境变量
# ==========================================

function Configure-Env {
    Print-Step "3/7 配置环境变量"

    $ENV_FILE = Join-Path $BACKEND_DIR ".env"
    $ENV_EXAMPLE = Join-Path $BACKEND_DIR ".env.example"

    if (Test-Path $ENV_FILE) {
        Print-Warning ".env 文件已存在"
        if (Test-Confirmation "是否覆盖现有的 .env 文件?") {
            Remove-Item $ENV_FILE
        }
        else {
            Print-Info "使用现有的 .env 文件"
            return
        }
    }

    # 获取用户输入
    Print-Info "请输入以下配置信息:"

    # MySQL 密码
    while ($true) {
        $MYSQL_PASSWORD = Read-Host "请输入 MySQL root 密码" -AsSecureString
        $MYSQL_PASSWORD_CONFIRM = Read-Host "请再次输入 MySQL root 密码" -AsSecureString

        $MYSQL_PASSWORD_PLAIN = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($MYSQL_PASSWORD))
        $MYSQL_PASSWORD_CONFIRM_PLAIN = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($MYSQL_PASSWORD_CONFIRM))

        if ($MYSQL_PASSWORD_PLAIN -eq $MYSQL_PASSWORD_CONFIRM_PLAIN) {
            break
        }
        else {
            Print-Error "两次输入的密码不一致，请重新输入"
        }
    }

    # DeepSeek API 密钥
    $DEEPSEEK_API_KEY = Read-Host "请输入 DeepSeek API 密钥 (留空跳过)"

    # SECRET_KEY
    $SECRET_KEY = "django-insecure-" + (-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ }))

    # 创建 .env 文件
    Print-Info "创建 .env 文件..."
    @"
SECRET_KEY=$SECRET_KEY
DEBUG=True

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=$MYSQL_PASSWORD_PLAIN
DB_NAME=$DB_NAME

DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
"@ | Out-File -FilePath $ENV_FILE -Encoding UTF8

    Print-Success ".env 文件创建成功"
}

# ==========================================
# 安装 Python 依赖
# ==========================================

function Install-PythonDeps {
    Print-Step "4/7 安装 Python 依赖"

    Print-Info "正在安装 Python 包，这可能需要几分钟..."

    Push-Location $BACKEND_DIR
    try {
        pip install -r requirements.txt
        Print-Success "Python 依赖安装完成"
    }
    catch {
        Print-Error "Python 依赖安装失败"
        exit 1
    }
    finally {
        Pop-Location
    }
}

# ==========================================
# 初始化数据库
# ==========================================

function Initialize-Database {
    Print-Step "5/7 初始化数据库"

    # 1. 创建数据库
    Print-Info "创建数据库..."
    Push-Location (Join-Path $BACKEND_DIR "scripts")
    try {
        python init_db.py
        Print-Success "数据库创建成功"
    }
    catch {
        Print-Error "数据库创建失败"
        exit 1
    }
    finally {
        Pop-Location
    }

    # 2. 执行 Django 迁移
    Print-Info "执行数据库迁移..."
    Push-Location $BACKEND_DIR
    try {
        python manage.py migrate
        Print-Success "数据库迁移完成"
    }
    catch {
        Print-Error "数据库 迁移失败"
        exit 1
    }
    finally {
        Pop-Location
    }

    # 3. 初始化数据
    Print-Info "初始化数据..."
    Push-Location (Join-Path $BACKEND_DIR "scripts")
    try {
        python init_data.py
        Print-Success "数据初始化完成"
    }
    catch {
        Print-Error "数据初始化失败"
        exit 1
    }
    finally {
        Pop-Location
    }
}

# ==========================================
# 安装前端依赖
# ==========================================

function Install-FrontendDeps {
    Print-Step "6/7 安装前端依赖"

    Print-Info "正在安装 npm 包，这可能需要几分钟..."

    Push-Location $FRONTEND_DIR
    try {
        npm install
        Print-Success "前端依赖安装完成"
    }
    catch {
        Print-Error "前端依赖安装失败"
        exit 1
    }
    finally {
        Pop-Location
    }
}

# ==========================================
# 完成提示
# ==========================================

function Print-Completion {
    Print-Step "7/7 安装完成"

    Write-ColorOutput ""
    Write-ColorOutput "🎉 恭喜！Cell-Yolo 安装完成！" "Green"
    Write-ColorOutput ""

    Write-ColorOutput "接下来，请在两个终端中分别运行以下命令：" "White"
    Write-ColorOutput ""
    Write-ColorOutput "终端 1 - 启动后端:" "Yellow"
    Write-ColorOutput "  cd $BACKEND_DIR" "White"
    Write-ColorOutput "  conda activate $CONDA_ENV_NAME" "White"
    Write-ColorOutput "  python manage.py runserver" "White"
    Write-ColorOutput ""
    Write-ColorOutput "终端 2 - 启动前端:" "Yellow"
    Write-ColorOutput "  cd $FRONTEND_DIR" "White"
    Write-ColorOutput "  npm run dev" "White"
    Write-ColorOutput ""
    Write-ColorOutput "启动成功后，访问以下地址：" "White"
    Write-ColorOutput "  前端应用: http://localhost:5173" "Cyan"
    Write-ColorOutput "  后端 API:  http://localhost:8000/api/test/" "Cyan"
    Write-ColorOutput "  管理后台:  http://localhost:8000/admin/" "Cyan"
    Write-ColorOutput ""
    Write-ColorOutput "默认管理员账号:" "White"
    Write-ColorOutput "  用户名: root" "White"
    Write-ColorOutput "  密码: password" "White"
    Write-ColorOutput ""
}

# ==========================================
# 主函数
# ==========================================

function Main {
    Write-ColorOutput ""
    Write-ColorOutput "╔═══════════════════════════════════════════════════════╗" "Cyan"
    Write-ColorOutput "║       Cell-Yolo 自动化安装脚本 (Windows)              ║" "Cyan"
    Write-ColorOutput "╚═══════════════════════════════════════════════════════╝" "Cyan"
    Write-ColorOutput ""

    # 检查是否在正确的目录（通过关键文件验证）
    $QUICKSTART_PATH = Join-Path $PROJECT_ROOT "web\QUICK-START.md"
    if (-not (Test-Path $QUICKSTART_PATH)) {
        Print-Error "未找到 QUICK-START.md，请确保脚本位于项目的 web 目录下"
        Print-Info "预期位置: $QUICKSTART_PATH"
        exit 1
    }

    Print-Info "项目根目录: $PROJECT_ROOT"

    # 执行安装步骤
    Check-Environment
    Setup-CondaEnv
    Configure-Env
    Install-PythonDeps
    Initialize-Database
    Install-FrontendDeps
    Print-Completion

    Print-Success "所有安装步骤已完成！"
}

# 运行主函数
Main