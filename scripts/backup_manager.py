# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
备份管理器脚本
用于管理ClawAI生产环境的备份和恢复
"""

import schedule
import time
import os
import sys
import shutil
import json
import sqlite3
import zipfile
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class BackupManager:
    """备份管理器"""
    
    def __init__(self, backup_dir: str = "backups", retention_days: int = 30):
        """
        初始化备份管理器
        
        Args:
            backup_dir: 备份目录
            retention_days: 保留天数
        """
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        
        # 确保备份目录存在
        self.backup_dir.mkdir(exist_ok=True, parents=True)
        
        # 关键文件路径
        self.critical_files = [
            "clawai_production.db",
            ".env.production",
            "config.py",
            "backend/auth/advanced_auth.py",
            "backend/auth/rbac.py",
            "backend/security/audit.py",
            "backend/ai_core/enhanced_llm_orchestrator.py",
            "backend/tools/tool_manager.py",
        ]
        
        # 关键目录
        self.critical_dirs = [
            "backend",
            "frontend/src",
            "configs",
            "scripts",
        ]
    
    def create_full_backup(self) -> Dict[str, Any]:
        """创建完整备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"clawai_full_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        print(f"[文件] 开始创建完整备份: {backup_name}")
        
        try:
            # 创建备份目录结构
            backup_path.mkdir(exist_ok=True)
            
            backup_info = {
                "backup_id": backup_name,
                "backup_type": "full",
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "components": [],
                "file_count": 0,
                "total_size_bytes": 0,
                "status": "in_progress"
            }
            
            # 1. 备份数据库
            db_backup = self._backup_database(backup_path)
            if db_backup["success"]:
                backup_info["components"].append("database")
                backup_info["file_count"] += db_backup["file_count"]
                backup_info["total_size_bytes"] += db_backup["size_bytes"]
                print(f"  [成功] 数据库备份完成: {db_backup['file_count']} 个文件")
            else:
                print(f"  [警告]  数据库备份失败: {db_backup.get('error', '未知错误')}")
            
            # 2. 备份配置文件
            config_backup = self._backup_configs(backup_path)
            if config_backup["success"]:
                backup_info["components"].append("configs")
                backup_info["file_count"] += config_backup["file_count"]
                backup_info["total_size_bytes"] += config_backup["size_bytes"]
                print(f"  [成功] 配置文件备份完成: {config_backup['file_count']} 个文件")
            
            # 3. 备份源代码
            source_backup = self._backup_source_code(backup_path)
            if source_backup["success"]:
                backup_info["components"].append("source_code")
                backup_info["file_count"] += source_backup["file_count"]
                backup_info["total_size_bytes"] += source_backup["size_bytes"]
                print(f"  [成功] 源代码备份完成: {source_backup['file_count']} 个文件")
            
            # 4. 备份用户数据
            user_data_backup = self._backup_user_data(backup_path)
            if user_data_backup["success"]:
                backup_info["components"].append("user_data")
                backup_info["file_count"] += user_data_backup["file_count"]
                backup_info["total_size_bytes"] += user_data_backup["size_bytes"]
                print(f"  [成功] 用户数据备份完成: {user_data_backup['file_count']} 个文件")
            
            # 5. 创建备份元数据
            backup_info["status"] = "completed"
            backup_info["checksum"] = self._calculate_backup_checksum(backup_path)
            
            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            # 6. 创建压缩包
            zip_path = self._create_backup_archive(backup_path)
            
            # 7. 清理临时目录
            shutil.rmtree(backup_path)
            
            backup_info["archive_path"] = str(zip_path)
            backup_info["archive_size_mb"] = round(os.path.getsize(zip_path) / (1024*1024), 2)
            
            print(f"[成功] 完整备份创建完成: {zip_path}")
            print(f"[统计] 备份统计: {backup_info['file_count']} 个文件, {backup_info['archive_size_mb']} MB")
            
            return backup_info
            
        except Exception as e:
            print(f"[失败] 备份创建失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 清理失败的备份
            if backup_path.exists():
                shutil.rmtree(backup_path, ignore_errors=True)
            
            return {
                "backup_id": backup_name,
                "status": "failed",
                "error": str(e)
            }
    
    def _backup_database(self, backup_path: Path) -> Dict[str, Any]:
        """备份数据库"""
        db_path = Path("clawai_production.db")
        db_backup_dir = backup_path / "database"
        db_backup_dir.mkdir(exist_ok=True)
        
        if not db_path.exists():
            return {
                "success": False,
                "error": "数据库文件不存在",
                "file_count": 0,
                "size_bytes": 0
            }
        
        try:
            # 复制数据库文件
            backup_db_path = db_backup_dir / db_path.name
            shutil.copy2(db_path, backup_db_path)
            
            # 创建数据库快照（SQL转储）
            sql_dump_path = db_backup_dir / "database_dump.sql"
            self._dump_database_to_sql(db_path, sql_dump_path)
            
            file_count = 2 if sql_dump_path.exists() else 1
            size_bytes = os.path.getsize(backup_db_path)
            if sql_dump_path.exists():
                size_bytes += os.path.getsize(sql_dump_path)
            
            return {
                "success": True,
                "file_count": file_count,
                "size_bytes": size_bytes,
                "files": [str(backup_db_path), str(sql_dump_path) if sql_dump_path.exists() else None]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_count": 0,
                "size_bytes": 0
            }
    
    def _dump_database_to_sql(self, db_path: Path, output_path: Path):
        """将数据库转储为SQL文件"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                # 获取所有表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    
                    # 获取表结构
                    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                    create_table_sql = cursor.fetchone()[0]
                    
                    f.write(f"{create_table_sql};\n\n")
                    
                    # 获取表数据
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    
                    if rows:
                        # 获取列名
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in cursor.fetchall()]
                        
                        for row in rows:
                            values = []
                            for value in row:
                                if value is None:
                                    values.append("NULL")
                                elif isinstance(value, str):
                                    values.append(f"'{value.replace("'", "''")}'")
                                elif isinstance(value, (int, float)):
                                    values.append(str(value))
                                elif isinstance(value, bytes):
                                    values.append(f"X'{value.hex()}'")
                                else:
                                    values.append(f"'{str(value)}'")
                            
                            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});"
                            f.write(f"{insert_sql}\n")
                    
                    f.write("\n")
            
            conn.close()
            
        except Exception as e:
            print(f"[警告]  数据库转储失败: {e}")
    
    def _backup_configs(self, backup_path: Path) -> Dict[str, Any]:
        """备份配置文件"""
        config_backup_dir = backup_path / "configs"
        config_backup_dir.mkdir(exist_ok=True)
        
        file_count = 0
        size_bytes = 0
        
        try:
            # 备份关键配置文件
            for config_file in self.critical_files:
                config_path = Path(config_file)
                if config_path.exists():
                    backup_file_path = config_backup_dir / config_path.name
                    
                    # 对于.env.production，移除敏感信息
                    if config_file == ".env.production":
                        self._backup_env_without_secrets(config_path, backup_file_path)
                    else:
                        shutil.copy2(config_path, backup_file_path)
                    
                    file_count += 1
                    size_bytes += os.path.getsize(backup_file_path)
            
            return {
                "success": True,
                "file_count": file_count,
                "size_bytes": size_bytes
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_count": file_count,
                "size_bytes": size_bytes
            }
    
    def _backup_env_without_secrets(self, source_path: Path, dest_path: Path):
        """备份.env文件，移除敏感信息"""
        with open(source_path, 'r', encoding='utf-8') as src:
            lines = src.readlines()
        
        with open(dest_path, 'w', encoding='utf-8') as dst:
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    parts = stripped.split('=', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        
                        # 隐藏敏感密钥
                        if any(secret in key.lower() for secret in ['key', 'secret', 'password', 'token']):
                            if value:
                                # 保留最后4个字符用于识别
                                masked = '*' * 8 + value[-4:] if len(value) > 4 else '*' * 8
                                dst.write(f"{key}={masked}\n")
                            else:
                                dst.write(f"{key}=\n")
                        else:
                            dst.write(line)
                else:
                    dst.write(line)
    
    def _backup_source_code(self, backup_path: Path) -> Dict[str, Any]:
        """备份源代码"""
        source_backup_dir = backup_path / "source_code"
        source_backup_dir.mkdir(exist_ok=True)
        
        file_count = 0
        size_bytes = 0
        
        try:
            # 备份关键目录
            for dir_path in self.critical_dirs:
                dir_full_path = Path(dir_path)
                if dir_full_path.exists():
                    backup_dir_path = source_backup_dir / dir_path
                    shutil.copytree(dir_full_path, backup_dir_path, 
                                  ignore=shutil.ignore_patterns('*.pyc', '__pycache__', 'node_modules', '.git'))
                    
                    # 统计文件数量和大小
                    for root, dirs, files in os.walk(backup_dir_path):
                        file_count += len(files)
                        for file in files:
                            file_path = os.path.join(root, file)
                            size_bytes += os.path.getsize(file_path)
            
            return {
                "success": True,
                "file_count": file_count,
                "size_bytes": size_bytes
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_count": file_count,
                "size_bytes": size_bytes
            }
    
    def _backup_user_data(self, backup_path: Path) -> Dict[str, Any]:
        """备份用户数据"""
        user_data_backup_dir = backup_path / "user_data"
        user_data_backup_dir.mkdir(exist_ok=True)
        
        file_count = 0
        size_bytes = 0
        
        try:
            # 备份用户上传的文件
            upload_dirs = ["uploads", "results", "logs"]
            
            for upload_dir in upload_dirs:
                upload_path = Path(upload_dir)
                if upload_path.exists():
                    backup_upload_path = user_data_backup_dir / upload_dir
                    shutil.copytree(upload_path, backup_upload_path,
                                  ignore=shutil.ignore_patterns('*.tmp', '*.temp'))
                    
                    # 统计文件数量和大小
                    for root, dirs, files in os.walk(backup_upload_path):
                        file_count += len(files)
                        for file in files:
                            file_path = os.path.join(root, file)
                            size_bytes += os.path.getsize(file_path)
            
            return {
                "success": True,
                "file_count": file_count,
                "size_bytes": size_bytes
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_count": file_count,
                "size_bytes": size_bytes
            }
    
    def _calculate_backup_checksum(self, backup_path: Path) -> str:
        """计算备份的校验和"""
        hash_md5 = hashlib.md5()
        
        # 遍历所有文件并计算哈希
        for root, dirs, files in os.walk(backup_path):
            for file in sorted(files):  # 排序确保一致性
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_md5.update(chunk)
                except:
                    pass
        
        return hash_md5.hexdigest()
    
    def _create_backup_archive(self, backup_path: Path) -> Path:
        """创建备份压缩包"""
        zip_path = self.backup_dir / f"{backup_path.name}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_path.parent)
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def create_incremental_backup(self) -> Dict[str, Any]:
        """创建增量备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"clawai_incremental_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        print(f"[文件] 开始创建增量备份: {backup_name}")
        
        try:
            # 获取最新的完整备份
            latest_full_backup = self._get_latest_backup("full")
            
            if not latest_full_backup:
                print("  ℹ️  未找到完整备份，创建完整备份代替")
                return self.create_full_backup()
            
            backup_path.mkdir(exist_ok=True)
            
            backup_info = {
                "backup_id": backup_name,
                "backup_type": "incremental",
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "base_backup": latest_full_backup["backup_id"],
                "components": [],
                "file_count": 0,
                "total_size_bytes": 0,
                "status": "in_progress"
            }
            
            # TODO: 实现增量备份逻辑
            # 比较文件变化，只备份修改过的文件
            
            backup_info["status"] = "completed"
            
            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            # 创建压缩包
            zip_path = self._create_backup_archive(backup_path)
            
            # 清理临时目录
            shutil.rmtree(backup_path)
            
            backup_info["archive_path"] = str(zip_path)
            backup_info["archive_size_mb"] = round(os.path.getsize(zip_path) / (1024*1024), 2)
            
            print(f"[成功] 增量备份创建完成: {zip_path}")
            
            return backup_info
            
        except Exception as e:
            print(f"[失败] 增量备份创建失败: {e}")
            return {
                "backup_id": backup_name,
                "status": "failed",
                "error": str(e)
            }
    
    def _get_latest_backup(self, backup_type: str = None) -> Optional[Dict[str, Any]]:
        """获取最新的备份"""
        backups = self.list_backups()
        
        if not backups:
            return None
        
        if backup_type:
            backups = [b for b in backups if b.get("backup_type") == backup_type]
        
        if not backups:
            return None
        
        # 按时间排序，获取最新的
        backups.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return backups[0]
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.zip"):
            try:
                # 从压缩包中提取元数据
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    if "backup_metadata.json" in zipf.namelist():
                        with zipf.open("backup_metadata.json") as f:
                            metadata = json.load(f)
                            metadata["archive_path"] = str(backup_file)
                            metadata["archive_size_mb"] = round(backup_file.stat().st_size / (1024*1024), 2)
                            backups.append(metadata)
            except:
                # 如果是旧格式的备份文件
                backup_info = {
                    "backup_id": backup_file.stem,
                    "backup_type": "unknown",
                    "timestamp": datetime.fromtimestamp(backup_file.stat().st_mtime).strftime("%Y%m%d_%H%M%S"),
                    "archive_path": str(backup_file),
                    "archive_size_mb": round(backup_file.stat().st_size / (1024*1024), 2),
                    "status": "legacy"
                }
                backups.append(backup_info)
        
        return backups
    
    def restore_backup(self, backup_id: str, restore_path: str = ".") -> Dict[str, Any]:
        """恢复备份"""
        print(f"🔄 开始恢复备份: {backup_id}")
        
        # 查找备份文件
        backup_file = None
        for file in self.backup_dir.glob("*.zip"):
            if backup_id in file.stem:
                backup_file = file
                break
        
        if not backup_file:
            return {
                "success": False,
                "error": f"备份文件不存在: {backup_id}"
            }
        
        restore_dir = Path(restore_path)
        restore_dir.mkdir(exist_ok=True)
        
        try:
            # 创建临时解压目录
            temp_dir = self.backup_dir / f"restore_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_dir.mkdir(exist_ok=True)
            
            # 解压备份文件
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # 读取元数据
            metadata_file = temp_dir / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {"backup_type": "unknown"}
            
            # 恢复文件
            restored_files = []
            
            # 恢复数据库
            db_source = temp_dir / "database" / "clawai_production.db"
            if db_source.exists():
                db_dest = restore_dir / "clawai_production_restored.db"
                shutil.copy2(db_source, db_dest)
                restored_files.append(str(db_dest))
                print(f"  [成功] 数据库恢复完成: {db_dest}")
            
            # 恢复配置文件
            configs_source = temp_dir / "configs"
            if configs_source.exists():
                for config_file in configs_source.iterdir():
                    config_dest = restore_dir / config_file.name
                    shutil.copy2(config_file, config_dest)
                    restored_files.append(str(config_dest))
                print(f"  [成功] 配置文件恢复完成: {len(list(configs_source.iterdir()))} 个文件")
            
            # 恢复源代码
            source_source = temp_dir / "source_code"
            if source_source.exists():
                for item in source_source.iterdir():
                    item_dest = restore_dir / item.name
                    if item.is_dir():
                        shutil.copytree(item, item_dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, item_dest)
                    restored_files.append(str(item_dest))
                print(f"  [成功] 源代码恢复完成")
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            print(f"[成功] 备份恢复完成: {backup_id}")
            
            return {
                "success": True,
                "backup_id": backup_id,
                "restored_files": restored_files,
                "restore_path": str(restore_dir),
                "metadata": metadata
            }
            
        except Exception as e:
            print(f"[失败] 备份恢复失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def cleanup_old_backups(self) -> Dict[str, Any]:
        """清理旧的备份"""
        print("🧹 清理旧的备份文件...")
        
        backups = self.list_backups()
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        deleted_files = []
        kept_files = []
        
        for backup in backups:
            backup_file = Path(backup["archive_path"])
            
            # 从文件名中提取时间戳
            timestamp_str = backup.get("timestamp", "")
            if timestamp_str:
                try:
                    backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                except:
                    # 如果无法解析时间戳，使用文件修改时间
                    backup_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
            else:
                backup_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            if backup_date < cutoff_date:
                try:
                    backup_file.unlink()
                    deleted_files.append(str(backup_file))
                    print(f"  🗑️  删除旧备份: {backup_file.name}")
                except Exception as e:
                    print(f"  [警告]  删除失败 {backup_file.name}: {e}")
            else:
                kept_files.append(str(backup_file))
        
        return {
            "deleted_count": len(deleted_files),
            "kept_count": len(kept_files),
            "deleted_files": deleted_files,
            "kept_files": kept_files
        }
    
    def schedule_backup_job(self, backup_type: str = "full", interval_hours: int = 24):
        """调度备份任务"""
        print(f"⏰ 调度备份任务: {backup_type} 备份, 每 {interval_hours} 小时")
        
        if backup_type == "full":
            schedule.every(interval_hours).hours.do(self.create_full_backup)
        elif backup_type == "incremental":
            schedule.every(interval_hours).hours.do(self.create_incremental_backup)
        
        # 同时调度清理任务（每天一次）
        schedule.every().day.do(self.cleanup_old_backups)
        
        return True
    
    def run_scheduled_backups(self, run_once: bool = False):
        """运行调度的备份任务"""
        print("🚀 开始运行调度备份任务")
        print("按 Ctrl+C 停止")
        
        try:
            if run_once:
                # 运行一次所有任务
                schedule.run_all()
                print("[成功] 一次性任务执行完成")
            else:
                # 持续运行
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            print("\n🛑 备份任务已停止")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ClawAI 备份管理器')
    parser.add_argument('--create-full', action='store_true', help='创建完整备份')
    parser.add_argument('--create-incremental', action='store_true', help='创建增量备份')
    parser.add_argument('--list', action='store_true', help='列出所有备份')
    parser.add_argument('--restore', type=str, help='恢复指定备份')
    parser.add_argument('--cleanup', action='store_true', help='清理旧备份')
    parser.add_argument('--schedule', type=str, choices=['full', 'incremental'], help='调度备份任务')
    parser.add_argument('--interval', type=int, default=24, help='调度间隔（小时）')
    parser.add_argument('--run-once', action='store_true', help='运行一次调度任务')
    parser.add_argument('--backup-dir', type=str, default='backups', help='备份目录')
    parser.add_argument('--retention-days', type=int, default=30, help='保留天数')
    
    args = parser.parse_args()
    
    try:
        # 创建备份管理器
        manager = BackupManager(
            backup_dir=args.backup_dir,
            retention_days=args.retention_days
        )
        
        print("🔧 ClawAI 备份管理器")
        print("=" * 60)
        
        if args.create_full:
            result = manager.create_full_backup()
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        elif args.create_incremental:
            result = manager.create_incremental_backup()
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        elif args.list:
            backups = manager.list_backups()
            if backups:
                print(f"[列表] 找到 {len(backups)} 个备份:")
                for backup in backups:
                    print(f"  • {backup['backup_id']} ({backup.get('backup_type', 'unknown')})")
                    print(f"    时间: {backup.get('timestamp', '未知')}")
                    print(f"    大小: {backup.get('archive_size_mb', 0)} MB")
                    print(f"    状态: {backup.get('status', 'unknown')}")
                    print()
            else:
                print("📭 没有找到备份")
        
        elif args.restore:
            result = manager.restore_backup(args.restore)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        elif args.cleanup:
            result = manager.cleanup_old_backups()
            print(f"🧹 清理完成:")
            print(f"  删除: {result['deleted_count']} 个文件")
            print(f"  保留: {result['kept_count']} 个文件")
        
        elif args.schedule:
            manager.schedule_backup_job(args.schedule, args.interval)
            manager.run_scheduled_backups(args.run_once)
        
        else:
            # 默认显示帮助
            parser.print_help()
        
        return 0
        
    except Exception as e:
        print(f"[失败] 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())