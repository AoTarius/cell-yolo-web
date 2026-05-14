#!/bin/bash

# ==========================================
# Cell-Yolo 自动化安装脚本
# ==========================================
# 此脚本会自动执行 QUICK-START.md 中的步骤
# 在需要用户输入的地方会提示输入
#
# 使用方法：
#   1. 在 web 目录下运行: ./setup.sh
#   2. 从其他位置运行: cd /path/to/project/web && ./setup.sh
#   3. 使用绝对路径运行: /path/to/project/web/setup.sh
#
# 注意：脚本必须位于项目的 web 目录下
# ==========================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 项目根目录（脚本在 web 目录下，所以项目根目录是 web 的上一级）
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 配置变量
CONDA_ENV_NAME="cell-yolo"
PYTHON_VERSION="3.8"
DB_NAME="cell_tracking"
BACKEND_DIR="$PROJECT_ROOT/web/backend"
FRONTEND_DIR="$PROJECT_ROOT/web/frontend"

# ==========================================
# 工具函数
# ==========================================

print_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 确认提示
confirm() {
    while true; do
        read -p "$1 (y/n): " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "请输入 y 或 n";;
        esac
    done
}

# ==========================================
# 环境检查
# ==========================================

check_environment() {
    print_step "1/7 检查系统环境"

    # 检查 conda
    if command_exists conda; then
        print_success "已找到 conda"
    else
        print_error "未找到 conda，请先安装 Anaconda 或 Miniconda"
        echo "下载地址: https://docs.conda.io/en/latest/miniconda.html"
        exit 1
    fi

    # 检查 MySQL
    if command_exists mysql; then
        print_success "已找到 MySQL"
    else
        print_warning "未找到 MySQL"
        if confirm "是否自动安装 MySQL (需要 Homebrew)?"; then
            install_mysql
        else
            print_error "请手动安装 MySQL 后再运行此脚本"
            exit 1
        fi
    fi

    # 检查 Node.js
    if command_exists node; then
        NODE_VERSION=$(node -v | sed 's/v//')
        print_success "已找到 Node.js (版本: $NODE_VERSION)"
    else
        print_error "未找到 Node.js"
        echo "请安装 Node.js ^20.19.0 或 >=22.12.0"
        echo "下载地址: https://nodejs.org/"
        exit 1
    fi

    # 检查 npm
    if command_exists npm; then
        print_success "已找到 npm"
    else
        print_error "未找到 npm"
        exit 1
    fi

    print_success "环境检查完成"
}

# ==========================================
# 安装 MySQL
# ==========================================

install_mysql() {
    print_info "正在使用 Homebrew 安装 MySQL..."
    if ! brew install mysql; then
        print_error "MySQL 安装失败"
        exit 1
    fi

    print_info "启动 MySQL 服务..."
    brew services start mysql

    print_warning "请设置 MySQL root 密码"
    mysql_secure_installation

    print_success "MySQL 安装完成"
}

# ==========================================
# 创建和激活 conda 环境
# ==========================================

setup_conda_env() {
    print_step "2/7 设置 Python 虚拟环境"

    # 检查环境是否已存在
    if conda env list | grep -q "^${CONDA_ENV_NAME} "; then
        print_warning "Conda 环境 '$CONDA_ENV_NAME' 已存在"
        if confirm "是否删除并重新创建环境?"; then
            conda env remove -n "$CONDA_ENV_NAME" -y
            print_info "正在创建 conda 环境..."
            conda create -n "$CONDA_ENV_NAME" python="$PYTHON_VERSION" -y
            print_success "Conda 环境创建成功"
        else
            print_info "使用现有的 conda 环境"
        fi
    else
        print_info "正在创建 conda 环境..."
        conda create -n "$CONDA_ENV_NAME" python="$PYTHON_VERSION" -y
        print_success "Conda 环境创建成功"
    fi

    # 激活环境
    print_info "激活 conda 环境..."
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$CONDA_ENV_NAME"
    print_success "Conda 环境已激活"
}

# ==========================================
# 配置环境变量
# ==========================================

configure_env() {
    print_step "3/7 配置环境变量"

    ENV_FILE="$BACKEND_DIR/.env"
    ENV_EXAMPLE="$BACKEND_DIR/.env.example"

    if [ -f "$ENV_FILE" ]; then
        print_warning ".env 文件已存在"
        if confirm "是否覆盖现有的 .env 文件?"; then
            rm "$ENV_FILE"
        else
            print_info "使用现有的 .env 文件"
            return
        fi
    fi

    # 获取用户输入
    print_info "请输入以下配置信息:"

    # MySQL 密码
    while true; do
        read -sp "请输入 MySQL root 密码: " MYSQL_PASSWORD
        echo
        read -sp "请再次输入 MySQL root 密码: " MYSQL_PASSWORD_CONFIRM
        echo
        if [ "$MYSQL_PASSWORD" = "$MYSQL_PASSWORD_CONFIRM" ]; then
            break
        else
            print_error "两次输入的密码不一致，请重新输入"
        fi
    done

    # DeepSeek API 密钥
    read -p "请输入 DeepSeek API 密钥 (留空跳过): " DEEPSEEK_API_KEY

    # SECRET_KEY
    SECRET_KEY="django-insecure-$(openssl rand -hex 32)"

    # 创建 .env 文件
    print_info "创建 .env 文件..."
    cat > "$ENV_FILE" << EOF
SECRET_KEY=$SECRET_KEY
DEBUG=True

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=$MYSQL_PASSWORD
DB_NAME=$DB_NAME

DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
EOF

    print_success ".env 文件创建成功"
}

# ==========================================
# 安装 Python 依赖
# ==========================================

install_python_deps() {
    print_step "4/7 安装 Python 依赖"

    print_info "正在安装 Python 包，这可能需要几分钟..."

    if ! (cd "$BACKEND_DIR" && pip install -r requirements.txt); then
        print_error "Python 依赖安装失败"
        exit 1
    fi

    print_success "Python 依赖安装完成"
}

# ==========================================
# 初始化数据库
# ==========================================

init_database() {
    print_step "5/7 初始化数据库"

    # 读取 MySQL 密码
    source "$BACKEND_DIR/.env"

    # 1. 创建数据库
    print_info "创建数据库..."
    if (cd "$BACKEND_DIR/scripts" && python init_db.py); then
        print_success "数据库创建成功"
    else
        print_error "数据库创建失败"
        exit 1
    fi

    # 2. 执行 Django 迁移
    print_info "执行数据库迁移..."
    if (cd "$BACKEND_DIR" && python manage.py migrate); then
        print_success "数据库迁移完成"
    else
        print_error "数据库迁移失败"
        exit 1
    fi

    # 3. 初始化数据
    print_info "初始化数据..."
    if (cd "$BACKEND_DIR/scripts" && python init_data.py); then
        print_success "数据初始化完成"
    else
        print_error "数据初始化失败"
        exit 1
    fi
}

# ==========================================
# 安装前端依赖
# ==========================================

install_frontend_deps() {
    print_step "6/7 安装前端依赖"

    print_info "正在安装 npm 包，这可能需要几分钟..."

    if ! (cd "$FRONTEND_DIR" && npm install); then
        print_error "前端依赖安装失败"
        exit 1
    fi

    print_success "前端依赖安装完成"
}

# ==========================================
# 完成提示
# ==========================================

print_completion() {
    print_step "7/7 安装完成"

    echo -e "\n${GREEN}🎉 恭喜！Cell-Yolo 安装完成！${NC}\n"

    echo "接下来，请在两个终端中分别运行以下命令："
    echo ""
    echo -e "${YELLOW}终端 1 - 启动后端:${NC}"
    echo "  cd $BACKEND_DIR"
    echo "  conda activate $CONDA_ENV_NAME"
    echo "  python manage.py runserver"
    echo ""
    echo -e "${YELLOW}终端 2 - 启动前端:${NC}"
    echo "  cd $FRONTEND_DIR"
    echo "  npm run dev"
    echo ""
    echo "启动成功后，访问以下地址："
    echo "  前端应用: ${BLUE}http://localhost:5173${NC}"
    echo "  后端 API:  ${BLUE}http://localhost:8000/api/test/${NC}"
    echo "  管理后台:  ${BLUE}http://localhost:8000/admin/${NC}"
    echo ""
    echo "默认管理员账号:"
    echo "  用户名: root"
    echo "  密码: password"
    echo ""
}

# ==========================================
# 主函数
# ==========================================

main() {
    echo -e "\n${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║       Cell-Yolo 自动化安装脚本                          ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}\n"

    # 检查是否在正确的目录（通过关键文件验证）
    if [ ! -f "$PROJECT_ROOT/web/QUICK-START.md" ]; then
        print_error "未找到 QUICK-START.md，请确保脚本位于项目的 web 目录下"
        print_info "预期位置: $PROJECT_ROOT/web/QUICK-START.md"
        exit 1
    fi

    print_info "项目根目录: $PROJECT_ROOT"

    # 执行安装步骤
    check_environment
    setup_conda_env
    configure_env
    install_python_deps
    init_database
    install_frontend_deps
    print_completion

    print_success "所有安装步骤已完成！"
}

# 运行主函数
main