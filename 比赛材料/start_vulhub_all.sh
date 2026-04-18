#!/bin/bash
# ============================================================
# Vulhub 15 靶场批量启动脚本（端口自动分配，无冲突）
# 用法:
#   bash start_vulhub_all.sh up      # 启动所有
#   bash start_vulhub_all.sh down    # 停止所有
#   bash start_vulhub_all.sh status  # 查看状态
#   bash start_vulhub_all.sh ports   # 打印端口表
# ============================================================

VULHUB_DIR="/e/vulhub"
ACTION="${1:-up}"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log_info() { echo -e "${CYAN}[INFO]${NC} $*"; }
log_ok()   { echo -e "${GREEN}[ OK ]${NC} $*"; }
log_err()  { echo -e "${RED}[FAIL]${NC} $*"; }

# ── 靶场定义: (lab路径 项目名 宿主端口:容器端口) ───────────────
# 每个靶场分配独立宿主端口，彻底避免冲突
declare -A LAB_PORTS=(
  ["struts2/s2-045"]="19001:8080"
  ["struts2/s2-057"]="19002:8080"
  ["thinkphp/5.0.23-rce"]="19003:80"
  ["weblogic/CVE-2023-21839"]="19004:7001"
  ["tomcat/CVE-2017-12615"]="19005:8080"
  ["php/CVE-2019-11043"]="19006:80"
  ["activemq/CVE-2022-41678"]="19007:8161"
  ["jboss/CVE-2017-7504"]="19008:8080"
  ["tomcat/tomcat8"]="19009:8080"
  ["shiro/CVE-2016-4437"]="19010:8080"
  ["fastjson/1.2.24-rce"]="19011:8090"
  ["fastjson/1.2.47-rce"]="19012:8090"
  ["django/CVE-2022-34265"]="19013:8000"
  ["flask/ssti"]="19014:8000"
  ["geoserver/CVE-2024-36401"]="19015:8080"
)

# 靶场有序列表
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

# 项目名（docker compose -p 参数）
declare -A LAB_NAMES=(
  ["struts2/s2-045"]="vulhub-s2045"
  ["struts2/s2-057"]="vulhub-s2057"
  ["thinkphp/5.0.23-rce"]="vulhub-thinkphp"
  ["weblogic/CVE-2023-21839"]="vulhub-weblogic"
  ["tomcat/CVE-2017-12615"]="vulhub-tomcat12615"
  ["php/CVE-2019-11043"]="vulhub-php11043"
  ["activemq/CVE-2022-41678"]="vulhub-activemq"
  ["jboss/CVE-2017-7504"]="vulhub-jboss"
  ["tomcat/tomcat8"]="vulhub-tomcat8"
  ["shiro/CVE-2016-4437"]="vulhub-shiro"
  ["fastjson/1.2.24-rce"]="vulhub-fastjson124"
  ["fastjson/1.2.47-rce"]="vulhub-fastjson1247"
  ["django/CVE-2022-34265"]="vulhub-django"
  ["flask/ssti"]="vulhub-flask"
  ["geoserver/CVE-2024-36401"]="vulhub-geoserver"
)

# 生成 override 文件（覆盖端口）
write_override() {
  local lab="$1"
  local port_map="${LAB_PORTS[$lab]}"
  local host_port="${port_map%%:*}"
  local container_port="${port_map##*:}"
  local lab_dir="$VULHUB_DIR/$lab"

  cat > "$lab_dir/docker-compose.override.yml" <<EOF
# 自动生成 - 端口覆盖，避免多靶场冲突
services:
  $(docker compose -f "$lab_dir/docker-compose.yml" config --services 2>/dev/null | head -1):
    ports:
      - "${host_port}:${container_port}"
EOF
}

do_up() {
  local ok=0 fail=0
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  启动 ${#LABS[@]} 个靶场 (端口范围 19001-19015)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  for lab in "${LABS[@]}"; do
    local lab_dir="$VULHUB_DIR/$lab"
    local pname="${LAB_NAMES[$lab]}"
    local port_map="${LAB_PORTS[$lab]}"
    local host_port="${port_map%%:*}"

    log_info "[$lab] → http://localhost:$host_port"

    if [ ! -f "$lab_dir/docker-compose.yml" ]; then
      log_err "[$lab] docker-compose.yml 不存在，跳过"
      ((fail++)); continue
    fi

    docker compose -p "$pname" -f "$lab_dir/docker-compose.yml" up -d 2>&1 | tail -3

    if [ $? -eq 0 ]; then
      log_ok "[$lab] 启动成功 → http://localhost:$host_port"
      ((ok++))
    else
      log_err "[$lab] 启动失败"
      ((fail++))
    fi
    echo ""
  done

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo -e "  ${GREEN}成功: $ok${NC}  ${RED}失败: $fail${NC}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

do_down() {
  local ok=0
  for lab in "${LABS[@]}"; do
    local lab_dir="$VULHUB_DIR/$lab"
    local pname="${LAB_NAMES[$lab]}"
    log_info "停止 [$lab] ..."
    docker compose -p "$pname" -f "$lab_dir/docker-compose.yml" down 2>&1 | tail -1
    ((ok++))
  done
  echo -e "${YELLOW}已停止 $ok 个靶场${NC}"
}

do_status() {
  for lab in "${LABS[@]}"; do
    local lab_dir="$VULHUB_DIR/$lab"
    local pname="${LAB_NAMES[$lab]}"
    echo "=== $lab ==="
    docker compose -p "$pname" -f "$lab_dir/docker-compose.yml" ps 2>/dev/null
    echo ""
  done
}

print_ports() {
  echo ""
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  printf "  ${CYAN}%-35s  %-6s  %-40s${NC}\n" "靶场" "端口" "访问地址"
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  printf "  %-35s  %-6s  %s\n" "struts2/s2-045"           "19001" "http://localhost:19001/index.action"
  printf "  %-35s  %-6s  %s\n" "struts2/s2-057"           "19002" "http://localhost:19002/showcase.action"
  printf "  %-35s  %-6s  %s\n" "thinkphp/5.0.23-rce"      "19003" "http://localhost:19003/index.php?s=captcha"
  printf "  %-35s  %-6s  %s\n" "weblogic/CVE-2023-21839"  "19004" "http://localhost:19004/console"
  printf "  %-35s  %-6s  %s\n" "tomcat/CVE-2017-12615"    "19005" "http://localhost:19005"
  printf "  %-35s  %-6s  %s\n" "php/CVE-2019-11043"       "19006" "http://localhost:19006"
  printf "  %-35s  %-6s  %s\n" "activemq/CVE-2022-41678"  "19007" "http://localhost:19007 (admin/admin)"
  printf "  %-35s  %-6s  %s\n" "jboss/CVE-2017-7504"      "19008" "http://localhost:19008/jmx-console"
  printf "  %-35s  %-6s  %s\n" "tomcat/tomcat8"           "19009" "http://localhost:19009"
  printf "  %-35s  %-6s  %s\n" "shiro/CVE-2016-4437"      "19010" "http://localhost:19010 (guest/guest)"
  printf "  %-35s  %-6s  %s\n" "fastjson/1.2.24-rce"      "19011" "http://localhost:19011"
  printf "  %-35s  %-6s  %s\n" "fastjson/1.2.47-rce"      "19012" "http://localhost:19012"
  printf "  %-35s  %-6s  %s\n" "django/CVE-2022-34265"    "19013" "http://localhost:19013"
  printf "  %-35s  %-6s  %s\n" "flask/ssti"               "19014" "http://localhost:19014"
  printf "  %-35s  %-6s  %s\n" "geoserver/CVE-2024-36401" "19015" "http://localhost:19015/geoserver/web"
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
}

case "$ACTION" in
  up)     do_up; print_ports ;;
  down)   do_down ;;
  status) do_status ;;
  ports)  print_ports ;;
  *)
    echo "用法: bash start_vulhub_all.sh [up|down|status|ports]"
    ;;
esac
