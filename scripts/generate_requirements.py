#!/usr/bin/env python3
"""
生成项目依赖requirements.txt文件
扫描所有Python文件并提取导入的包
"""

import os
import ast
import sys
import re
from pathlib import Path
from typing import List, Set, Dict

# 已知的标准库模块（不需要安装）
STD_LIB_MODULES = {
    'os', 'sys', 'time', 'json', 're', 'pathlib', 'typing', 
    'collections', 'itertools', 'functools', 'datetime', 'logging',
    'subprocess', 'shutil', 'tempfile', 'urllib', 'socket', 'threading',
    'multiprocessing', 'hashlib', 'base64', 'random', 'math', 'statistics',
    'decimal', 'fractions', 'copy', 'pprint', 'textwrap', 'csv', 'xml',
    'html', 'email', 'uuid', 'queue', 'socketserver', 'http', 'ssl', 'ssl',
    'asyncio', 'concurrent', 'inspect', 'ast', 'importlib', 'pkgutil',
    'weakref', 'enum', 'types', 'dataclasses', 'contextlib', 'abc', 'io',
    'pickle', 'shelve', 'sqlite3', 'zipfile', 'tarfile', 'gzip', 'bz2',
    'lzma', 'zlib', 'csv', 'configparser', 'argparse', 'getopt', 'optparse',
    'readline', 'rlcompleter', 'getpass', 'curses', 'platform', 'errno',
    'ctypes', 'mmap', 'signal', 'traceback', 'linecache', 'code', 'codeop',
    'pdb', 'profile', 'cProfile', 'timeit', 'doctest', 'unittest', 'test',
    'sysconfig', 'site', 'os.path', 'pathlib.Path', 'builtins', '__future__',
    'typing', 'collections.abc'
}

# 项目内部模块映射到外部包名称
MODULE_MAPPING = {
    'flask': 'Flask',
    'flask_cors': 'flask-cors',
    'redis': 'redis',
    'pyotp': 'pyotp',
    'requests': 'requests',
    'pymongo': 'pymongo',
    'sqlalchemy': 'SQLAlchemy',
    'flask_sqlalchemy': 'Flask-SQLAlchemy',
    'flask_jwt_extended': 'flask-jwt-extended',
    'flask_login': 'Flask-Login',
    'flask_bcrypt': 'Flask-Bcrypt',
    'flask_migrate': 'Flask-Migrate',
    'flask_mail': 'Flask-Mail',
    'flask_wtf': 'Flask-WTF',
    'wtforms': 'WTForms',
    'email_validator': 'email-validator',
    'werkzeug': 'Werkzeug',
    'jinja2': 'Jinja2',
    'markupsafe': 'MarkupSafe',
    'itsdangerous': 'itsdangerous',
    'click': 'click',
    'blinker': 'blinker',
    'gunicorn': 'gunicorn',
    'eventlet': 'eventlet',
    'gevent': 'gevent',
    'psutil': 'psutil',
    'psycopg2': 'psycopg2-binary',
    'mysql.connector': 'mysql-connector-python',
    'pymysql': 'PyMySQL',
    'cryptography': 'cryptography',
    'pyjwt': 'PyJWT',
    'bcrypt': 'bcrypt',
    'passlib': 'passlib',
    'argon2': 'argon2-cffi',
    'pillow': 'Pillow',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'scipy': 'scipy',
    'matplotlib': 'matplotlib',
    'seaborn': 'seaborn',
    'plotly': 'plotly',
    'scikit_learn': 'scikit-learn',
    'tensorflow': 'tensorflow',
    'torch': 'torch',
    'keras': 'keras',
    'opencv': 'opencv-python',
    'pytesseract': 'pytesseract',
    'pytz': 'pytz',
    'tzlocal': 'tzlocal',
    'python_dateutil': 'python-dateutil',
    'arrow': 'arrow',
    'pendulum': 'pendulum',
    'celery': 'celery',
    'redis': 'redis',
    'pika': 'pika',
    'kombu': 'kombu',
    'django': 'Django',
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'starlette': 'starlette',
    'pydantic': 'pydantic',
    'httpx': 'httpx',
    'aiohttp': 'aiohttp',
    'tornado': 'tornado',
    'boto3': 'boto3',
    'botocore': 'botocore',
    'awscli': 'awscli',
    'azure': 'azure-common',
    'google.cloud': 'google-cloud-storage',
    'minio': 'minio',
    'paramiko': 'paramiko',
    'fabric': 'fabric',
    'invoke': 'invoke',
    'ansible': 'ansible',
    'docker': 'docker',
    'kubernetes': 'kubernetes',
    'openstack': 'openstacksdk',
    'libvirt': 'libvirt-python',
    'xmlrpclib': 'xmlrpc.client',
    'simplejson': 'simplejson',
    'ujson': 'ujson',
    'rapidjson': 'python-rapidjson',
    'orjson': 'orjson',
    'msgpack': 'msgpack',
    'cbor2': 'cbor2',
    'yaml': 'PyYAML',
    'toml': 'toml',
    'configparser': 'configparser',
    'dotenv': 'python-dotenv',
    'environs': 'environs',
    'dynaconf': 'dynaconf',
    'hvac': 'hvac',
    'vault': 'hvac',
    'consul': 'python-consul',
    'etcd3': 'etcd3',
    'zookeeper': 'kazoo',
    'kafka': 'kafka-python',
    'pulsar': 'pulsar-client',
    'rabbitmq': 'pika',
    'zmq': 'pyzmq',
    'grpc': 'grpcio',
    'thrift': 'thrift',
    'protobuf': 'protobuf',
    'avro': 'avro-python3',
    'capnproto': 'pycapnp',
    'flatbuffers': 'flatbuffers',
    'msgpack': 'msgpack',
    'cbor': 'cbor2',
    'bson': 'pymongo',
    'couchdb': 'couchdb',
    'cassandra': 'cassandra-driver',
    'riak': 'riak',
    'neo4j': 'neo4j',
    'arangodb': 'python-arango',
    'orientdb': 'pyorient',
    'influxdb': 'influxdb',
    'prometheus': 'prometheus-client',
    'graphite': 'graphite-api',
    'statsd': 'statsd',
    'elasticsearch': 'elasticsearch',
    'opensearch': 'opensearch-py',
    'solr': 'pysolr',
    'splunk': 'splunk-sdk',
    'logstash': 'logstash-formatter',
    'fluentd': 'fluent-logger',
    'graylog': 'graypy',
    'sentry': 'sentry-sdk',
    'loguru': 'loguru',
    'structlog': 'structlog',
    'colorlog': 'colorlog',
    'rich': 'rich',
    'tqdm': 'tqdm',
    'progress': 'progress',
    'alive_progress': 'alive-progress',
    'halo': 'halo',
    'spinners': 'spinners',
    'yaspin': 'yaspin',
    'click_spinner': 'click-spinner',
    'termcolor': 'termcolor',
    'colorama': 'colorama',
    'blessed': 'blessed',
    'prompt_toolkit': 'prompt_toolkit',
    'readline': 'gnureadline',
    'pyreadline': 'pyreadline3',
    'wcwidth': 'wcwidth',
    'asciimatics': 'asciimatics',
    'asciinema': 'asciinema',
    'pyfiglet': 'pyfiglet',
    'art': 'art',
    'emoji': 'emoji',
    'pygments': 'Pygments',
    'markdown': 'markdown',
    'mistune': 'mistune',
    'commonmark': 'commonmark',
    'markdown2': 'markdown2',
    'mdx': 'python-markdown-math',
    'recommonmark': 'recommonmark',
    'sphinx': 'sphinx',
    'mkdocs': 'mkdocs',
    'pdoc': 'pdoc',
    'sphinx_rtd_theme': 'sphinx-rtd-theme',
    'readthedocs': 'readthedocs-sphinx-ext',
    'nbsphinx': 'nbsphinx',
    'ipython': 'ipython',
    'jupyter': 'jupyter',
    'notebook': 'notebook',
    'jupyterlab': 'jupyterlab',
    'voila': 'voila',
    'nbconvert': 'nbconvert',
    'nbformat': 'nbformat',
    'ipykernel': 'ipykernel',
    'ipywidgets': 'ipywidgets',
    'widgetsnbextension': 'widgetsnbextension',
    'jupyter_contrib_nbextensions': 'jupyter-contrib-nbextensions',
    'jupyter_nbextensions_configurator': 'jupyter-nbextensions-configurator',
    'jupyterthemes': 'jupyterthemes',
    'jupyterlab_code_formatter': 'jupyterlab-code-formatter',
    'jupyterlab_git': 'jupyterlab-git',
    'jupyterlab_lsp': 'jupyterlab-lsp',
    'jupyterlab_widgets': 'jupyterlab-widgets',
    'jupyter_server': 'jupyter-server',
    'jupyter_client': 'jupyter-client',
    'jupyter_core': 'jupyter-core',
    'jupyter_console': 'jupyter-console',
    'qtconsole': 'qtconsole',
    'spyder': 'spyder',
    'spyder_kernels': 'spyder-kernels',
    'spyder_notebook': 'spyder-notebook',
    'spyder_unittest': 'spyder-unittest',
    'spyder_terminal': 'spyder-terminal',
    'spyder_line_profiler': 'spyder-line-profiler',
    'spyder_memory_profiler': 'spyder-memory-profiler',
    'spyder_reports': 'spyder-reports',
    'spyder_autopep8': 'spyder-autopep8',
    'spyder_vim': 'spyder-vim',
    'spyder_tensorboard': 'spyder-tensorboard',
    'spyder_profiler': 'spyder-profiler',
    'spyder_code_analysis': 'spyder-code-analysis',
    'spyder_io': 'spyder-io',
    'spyder_plugins': 'spyder-plugins',
    'spyder_api': 'spyder-api',
    'spyder_external_plugins': 'spyder-external-plugins'
}

def extract_imports(filepath: Path) -> Set[str]:
    """从Python文件中提取导入的模块"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                if module:
                    imports.add(module.split('.')[0])
        
        return imports
    except (SyntaxError, UnicodeDecodeError):
        # 文件可能不是Python文件或有语法错误
        return set()
    except Exception as e:
        print(f"解析文件 {filepath} 时出错: {e}")
        return set()

def is_standard_library(module: str) -> bool:
    """检查模块是否是Python标准库"""
    # 检查精确匹配
    if module in STD_LIB_MODULES:
        return True
    
    # 检查前缀匹配
    for std_module in STD_LIB_MODULES:
        if module.startswith(std_module.split('.')[0]):
            return True
    
    # 特殊处理：以_开头的可能是C扩展或内部模块
    if module.startswith('_'):
        return True
    
    return False

def map_to_package_name(module: str) -> str:
    """将导入的模块名映射到PyPI包名"""
    # 直接映射
    if module in MODULE_MAPPING:
        return MODULE_MAPPING[module]
    
    # 检查点号分隔的模块
    for key in MODULE_MAPPING:
        if module.startswith(key):
            return MODULE_MAPPING[key]
    
    # 默认情况下，模块名就是包名（小写）
    return module.lower()

def scan_project(project_root: Path) -> Dict[str, Set[str]]:
    """扫描项目中的所有Python文件"""
    all_imports = set()
    scanned_files = []
    
    # 需要扫描的目录
    scan_dirs = [
        project_root / 'backend',
        project_root / 'scripts',
        project_root / 'config',
        project_root / 'utils',
        project_root / 'tests'
    ]
    
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        
        for py_file in scan_dir.rglob('*.py'):
            if '__pycache__' in str(py_file) or '.pyc' in str(py_file):
                continue
            
            imports = extract_imports(py_file)
            if imports:
                scanned_files.append(str(py_file.relative_to(project_root)))
                all_imports.update(imports)
    
    return {
        'imports': all_imports,
        'files': scanned_files
    }

def generate_requirements(imports: Set[str]) -> List[str]:
    """生成requirements.txt内容"""
    requirements = []
    
    for module in sorted(imports):
        # 跳过标准库
        if is_standard_library(module):
            continue
        
        # 跳过项目内部模块（假设以backend、config、utils、scripts开头）
        if module.startswith(('backend', 'config', 'utils', 'scripts', 'tests')):
            continue
        
        # 获取包名
        package_name = map_to_package_name(module)
        
        # 添加到requirements
        if package_name not in requirements:
            requirements.append(package_name)
    
    # 添加已知必需但可能未检测到的包
    essential_packages = [
        'Flask',
        'flask-cors',
        'redis',
        'pyotp',
        'requests',
        'Werkzeug',
        'Jinja2',
        'itsdangerous',
        'click'
    ]
    
    for package in essential_packages:
        if package not in requirements:
            requirements.append(package)
    
    # 按字母顺序排序
    requirements.sort(key=str.lower)
    
    return requirements

def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    
    print("=" * 60)
    print("生成项目依赖文件")
    print("=" * 60)
    print(f"项目根目录: {project_root}")
    print()
    
    # 扫描项目
    print("扫描Python文件...")
    result = scan_project(project_root)
    imports = result['imports']
    scanned_files = result['files']
    
    print(f"扫描了 {len(scanned_files)} 个Python文件")
    print(f"发现 {len(imports)} 个不同的导入模块")
    print()
    
    # 显示检测到的导入
    print("检测到的导入模块:")
    for module in sorted(imports):
        if is_standard_library(module):
            print(f"  [STD]  {module}")
        elif module.startswith(('backend', 'config', 'utils', 'scripts', 'tests')):
            print(f"  [PROJ] {module}")
        else:
            print(f"  [EXT]  {module}")
    print()
    
    # 生成requirements
    print("生成requirements.txt...")
    requirements = generate_requirements(imports)
    
    print(f"需要安装 {len(requirements)} 个包:")
    for req in requirements:
        print(f"  - {req}")
    
    # 创建requirements.txt
    requirements_path = project_root / 'requirements.txt'
    with open(requirements_path, 'w', encoding='utf-8') as f:
        f.write("# ClawAI 项目依赖\n")
        f.write("# 生成时间: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
        f.write("# 使用: pip install -r requirements.txt\n")
        f.write("\n")
        
        for req in requirements:
            f.write(f"{req}\n")
    
    print(f"\n✅ requirements.txt 已生成: {requirements_path}")
    
    # 生成简化版requirements（仅核心依赖）
    core_requirements = [
        'Flask',
        'flask-cors',
        'redis',
        'pyotp',
        'requests'
    ]
    
    core_path = project_root / 'requirements-core.txt'
    with open(core_path, 'w', encoding='utf-8') as f:
        f.write("# ClawAI 核心依赖\n")
        f.write("# 仅包含运行API服务器所需的最少依赖\n")
        f.write("\n")
        
        for req in core_requirements:
            f.write(f"{req}\n")
    
    print(f"✅ 核心依赖文件已生成: {core_path}")
    
    # 生成安装脚本
    install_script_path = project_root / 'scripts' / 'install_dependencies.py'
    install_script_content = '''#!/usr/bin/env python3
"""
安装项目依赖脚本
自动安装requirements.txt中的所有依赖
"""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies(requirements_file: str = "requirements.txt"):
    """安装依赖"""
    project_root = Path(__file__).parent.parent
    req_path = project_root / requirements_file
    
    if not req_path.exists():
        print(f"❌ 依赖文件不存在: {req_path}")
        return False
    
    print(f"📦 安装依赖从: {req_path}")
    
    try:
        # 使用pip安装
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode == 0:
            print("✅ 依赖安装成功!")
            if result.stdout:
                print("安装输出:")
                print(result.stdout[:500])  # 只显示前500字符
            return True
        else:
            print("❌ 依赖安装失败!")
            print("错误信息:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 安装过程中发生异常: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("ClawAI 依赖安装工具")
    print("=" * 60)
    
    # 检查pip是否可用
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      capture_output=True, check=True)
    except Exception:
        print("❌ pip不可用，请先安装pip")
        return 1
    
    # 安装依赖
    success = install_dependencies()
    
    print("=" * 60)
    if success:
        print("✅ 所有依赖安装完成!")
        print("\n下一步:")
        print("1. 运行 'python backend/api_server.py' 启动API服务器")
        print("2. 或运行 'start.bat' 使用启动菜单")
        return 0
    else:
        print("❌ 依赖安装失败，请手动检查")
        return 1

if __name__ == '__main__':
    sys.exit(main())
'''
    
    with open(install_script_path, 'w', encoding='utf-8') as f:
        f.write(install_script_content)
    
    # 使脚本可执行
    if os.name != 'nt':  # 非Windows系统
        os.chmod(install_script_path, 0o755)
    
    print(f"✅ 依赖安装脚本已生成: {install_script_path}")
    
    print("\n" + "=" * 60)
    print("完成!")
    print("=" * 60)
    print("\n后续操作:")
    print(f"1. 安装所有依赖: pip install -r {requirements_path}")
    print(f"2. 仅安装核心依赖: pip install -r {core_path}")
    print(f"3. 使用安装脚本: python {install_script_path}")
    print("\n注意: 安全工具（如nmap、whatweb等）需要通过工具安装脚本单独安装")

if __name__ == '__main__':
    import time
    main()