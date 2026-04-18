#!/bin/bash
# ============================================================
# Vulhub 靶场批量启动脚本
# 靶场数量: 15
# 用法: bash start_vulhub.sh [up|down|status]
# ============================================================

VULHUB_DIR="E:/vulhub"
ACTION="${1:-up}"

# 15 个靶场路径
LABS=(
  "struts2/s2-045"
  "struts2/s2-057"
  "thinkphp/5.0.23-rce"
  "weblogic/CVE-2023-21839"
  "tomcat/CVE-2017-12615"
  "php/CVE-2019-11043"
  "activemq/CVE-2022-41678"
  "jboss/CVE-2017-7504"
  "tomcat/tomcat8"
  "shiro/CVE-2016-4437"
  "fastjson/1.2.24-rce"
  "fastjson/1.2.47-rce"
  "django/CVE-2022-34265"
  "flask/ssti"
  "geoserver/CVE-2024-36401"
)

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_err()   { echo -e "${RED}[ERR]${NC}   $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }

# ── Step 1: clone or update vulhub ──────────────────────────
clone_vulhub() {
  if [ -d "$VULHUB_DIR/.git" ]; then
    log_info "vulhub 已存在，执行 git pull 更新..."
    git -C "$VULHUB_DIR" pull --ff-only 2>&1 | tail -1
  else
    log_info "克隆 vulhub 到 $VULHUB_DIR ..."
    git clone --depth=1 https://github.com/vulhub/vulhub.git "$VULHUB_DIR"
    if [ $? -ne 0 ]; then
      log_err "clone 失败，请检查网络或手动下载 vulhub"
      exit 1
    fi
  fi
  log_ok "vulhub 准备完成"
}

# ── Step 2: 批量操作 ─────────────────────────────────────────
run_all() {
  local action="$1"
  local success=0
  local fail=0

  echo ""
  echo "============================================================"
  echo "  动作: $action  |  靶场数量: ${#LABS[@]}"
  echo "============================================================"

  for lab in "${LABS[@]}"; do
    local lab_dir="$VULHUB_DIR/$lab"
    if [ ! -f "$lab_dir/docker-compose.yml" ]; then
      log_warn "[$lab] docker-compose.yml 不存在，跳过"
      ((fail++))
      continue
    fi

    echo ""
    log_info "[$lab] 执行 docker compose $action ..."

    if [ "$action" = "up" ]; then
      docker compose -f "$lab_dir/docker-compose.yml" up -d 2>&1
    elif [ "$action" = "down" ]; then
      docker compose -f "$lab_dir/docker-compose.yml" down 2>&1
    elif [ "$action" = "status" ]; then
      docker compose -f "$lab_dir/docker-compose.yml" ps 2>&1
    fi

    if [ $? -eq 0 ]; then
      log_ok "[$lab] $action 成功"
      ((success++))
    else
      log_err "[$lab] $action 失败"
      ((fail++))
    fi
  done

  echo ""
  echo "============================================================"
  echo "  完成: 成功 ${success}，失败 ${fail}"
  echo "============================================================"
}

# ── Step 3: 启动后打印端口汇总 ──────────────────────────────
print_ports() {
  echo ""
  echo -e "${CYAN}============================================================"
  echo "  靶场访问地址汇总（容器暴露端口，需确认实际映射）"
  echo -e "============================================================${NC}"
  echo ""
  printf "  %-35s  %-10s  %s\n" "靶场" "默认端口" "访问地址"
  printf "  %-35s  %-10s  %s\n" "----" "--------" "--------"
  printf "  %-35s  %-10s  %s\n" "struts2/s2-045"            "8080" "http://localhost:8080/index.action"
  printf "  %-35s  %-10s  %s\n" "struts2/s2-057"            "8080" "http://localhost:8080/showcase.action"
  printf "  %-35s  %-10s  %s\n" "thinkphp/5.0.23-rce"       "8080" "http://localhost:8080/index.php?s=captcha"
  printf "  %-35s  %-10s  %s\n" "weblogic/CVE-2023-21839"   "7001" "http://localhost:7001/console"
  printf "  %-35s  %-10s  %s\n" "tomcat/CVE-2017-12615"     "8080" "http://localhost:8080"
  printf "  %-35s  %-10s  %s\n" "php/CVE-2019-11043"        "8080" "http://localhost:8080"
  printf "  %-35s  %-10s  %s\n" "activemq/CVE-2022-41678"   "8161" "http://localhost:8161 (admin/admin)"
  printf "  %-35s  %-10s  %s\n" "jboss/CVE-2017-7504"       "8080" "http://localhost:8080/jmx-console"
  printf "  %-35s  %-10s  %s\n" "tomcat/tomcat8"            "8080" "http://localhost:8080"
  printf "  %-35s  %-10s  %s\n" "shiro/CVE-2016-4437"       "8080" "http://localhost:8080 (guest/guest)"
  printf "  %-35s  %-10s  %s\n" "fastjson/1.2.24-rce"       "8090" "http://localhost:8090"
  printf "  %-35s  %-10s  %s\n" "fastjson/1.2.47-rce"       "8090" "http://localhost:8090"
  printf "  %-35s  %-10s  %s\n" "django/CVE-2022-34265"     "8000" "http://localhost:8000"
  printf "  %-35s  %-10s  %s\n" "flask/ssti"                "5000" "http://localhost:5000"
  printf "  %-35s  %-10s  %s\n" "geoserver/CVE-2024-36401"  "8080" "http://localhost:8080/geoserver/web"
  echo ""
  echo -e "${YELLOW}注意: 多个靶场使用相同端口(8080)时 docker-compose 会自动映射到其他端口，"
  echo -e "请用 'docker ps' 查看实际端口映射。${NC}"
  echo ""
}

# ── 主流程 ───────────────────────────────────────────────────
case "$ACTION" in
  up)
    clone_vulhub
    run_all "up"
    print_ports
    echo -e "${GREEN}全部靶场已启动！运行 'docker ps' 查看实际端口。${NC}"
    ;;
  down)
    run_all "down"
    echo -e "${YELLOW}全部靶场已停止。${NC}"
    ;;
  status)
    run_all "status"
    ;;
  *)
    echo "用法: bash start_vulhub.sh [up|down|status]"
    echo "  up     - 克隆/更新 vulhub 并启动所有靶场（默认）"
    echo "  down   - 停止所有靶场"
    echo "  status - 查看所有靶场容器状态"
    ;;
esac
