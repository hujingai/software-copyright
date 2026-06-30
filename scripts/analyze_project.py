#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目分析工具
扫描项目目录，分析语言、框架、文件结构、路由等信息。
用法: python analyze_project.py --project <项目路径> [--out <输出JSON>]
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, List, Optional

# 默认排除的目录
EXCLUDE_DIRS = {
    'node_modules', 'dist', 'build', '.git', '__pycache__', '.idea',
    'target', 'vendor', '.gradle', 'coverage', '.nyc_output',
    '.next', '.nuxt', 'output', 'out', '.cache', '.turbo',
    '软著申请资料', '软件著作权申请资料', '.codebuddy', '.codex',
}

# 默认排除的文件后缀
EXCLUDE_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp',
    '.mp3', '.mp4', '.wav', '.avi', '.mov', '.mkv',
    '.ttf', '.woff', '.woff2', '.eot', '.otf',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.tar', '.gz', '.rar', '.7z', '.jar', '.war',
    '.exe', '.dll', '.so', '.dylib', '.wasm',
    '.lock', '.map', '.min.js', '.min.css',
    '.db', '.sqlite', '.sqlite3',
}


# 语言推断规则
LANGUAGE_PATTERNS = {
    '.java': 'Java',
    '.py': 'Python',
    '.js': 'JavaScript',
    '.jsx': 'JavaScript/React',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript/React',
    '.vue': 'Vue.js',
    '.go': 'Go',
    '.rs': 'Rust',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.c': 'C',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.cs': 'C#',
    '.dart': 'Dart',
    '.scala': 'Scala',
}


def should_exclude_dir(dir_path: Path) -> bool:
    """判断是否应该排除该目录"""
    return any(part in EXCLUDE_DIRS or part.startswith('.') for part in dir_path.parts)


def is_source_file(file_path: Path) -> bool:
    """判断是否为源码文件"""
    suffix = file_path.suffix.lower()
    if suffix in EXCLUDE_EXTENSIONS:
        return False
    # 从语言规则中判断
    return suffix in LANGUAGE_PATTERNS


def is_config_file(file_name: str) -> bool:
    """判断是否为配置文件"""
    config_patterns = {
        'package.json', 'package-lock.json', 'tsconfig.json',
        'webpack.config', 'vite.config', 'rollup.config',
        '.eslintrc', '.prettierrc', '.babelrc',
        'dockerfile', 'makefile', '.env', '.gitignore',
        'requirements.txt', 'pom.xml', 'build.gradle',
        'cargo.toml', 'go.mod', 'gemfile', 'composer.json',
    }
    lower = file_name.lower()
    return any(pat in lower for pat in config_patterns)


def classify_file(file_path: Path, project_root: Path) -> str:
    """按功能分类文件"""
    relative = file_path.relative_to(project_root)
    path_str = str(relative).lower().replace('\\', '/')
    name = file_path.stem.lower()

    classification_rules = [
        (['index.', 'main.', 'app.', '_app.', 'server.'], 'entry'),
        (['router', 'routes', 'route'], 'route'),
        (['pages/', 'views/', 'screens/'], 'page'),
        (['components/', 'widgets/'], 'component'),
        (['api/', 'services/', 'service', 'controller', 'handler'], 'api_or_service'),
        (['model', 'entity', 'schema', 'dto', 'dao', 'repository', 'mapper'], 'model_or_data'),
        (['store', 'state', 'redux', 'vuex', 'pinia'], 'state'),
        (['util', 'utils', 'helper', 'helpers', 'common'], 'utility'),
        (['style', 'css', 'scss', 'less', '.module.'], 'style'),
        (['test', 'spec', '__tests__'], 'test'),
    ]

    for patterns, category in classification_rules:
        if any(pat in path_str or (not pat.endswith('/') and pat in name) for pat in patterns):
            return category

    return 'source'


def load_package_json(project_root: Path) -> Optional[dict]:
    """加载 package.json"""
    for candidate in [project_root / 'package.json',
                      project_root / 'frontend' / 'package.json',
                      project_root / 'web' / 'package.json']:
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, IOError):
                pass
    return None


def detect_frameworks(package: Optional[dict], ext_counts: Counter) -> List[str]:
    """检测使用的框架"""
    frameworks = []
    deps = {}
    if package:
        deps.update(package.get('dependencies', {}))
        deps.update(package.get('devDependencies', {}))

    dep_names = set(deps.keys())

    dep_framework_map = {
        'react': 'React', 'react-dom': 'React', 'vue': 'Vue.js',
        'next': 'Next.js', 'nuxt': 'Nuxt.js', 'angular': 'Angular',
        'svelte': 'Svelte', 'express': 'Express.js', 'koa': 'Koa',
        'fastify': 'Fastify', 'nestjs': 'NestJS', 'django': 'Django',
        'flask': 'Flask', 'fastapi': 'FastAPI', 'spring-boot': 'Spring Boot',
        'electron': 'Electron', 'tauri': 'Tauri', 'vite': 'Vite',
    }
    for dep, framework in dep_framework_map.items():
        if dep in dep_names:
            frameworks.append(framework)

    # 从文件后缀推断
    if '.vue' in ext_counts:
        if 'Vue.js' not in frameworks:
            frameworks.append('Vue.js')
    if '.tsx' in ext_counts and 'React' not in frameworks:
        if 'react' in dep_names:
            frameworks.append('React')
    if '.java' in ext_counts and 'Spring Boot' not in frameworks:
        frameworks.append('Java')

    return list(set(frameworks)) if frameworks else ['未检测到已知框架']


def infer_language(ext_counts: Counter) -> str:
    """推断主要编程语言"""
    lang_counts = Counter()
    for ext, count in ext_counts.items():
        lang = LANGUAGE_PATTERNS.get(ext, '')
        if lang:
            lang_counts[lang] += count

    if lang_counts:
        return lang_counts.most_common(1)[0][0]
    return '未知'


def extract_routes(project_root: Path) -> List[str]:
    """从源码中提取路由路径"""
    routes = []

    # Vue Router 格式: path: '/xxx'
    for route_file in project_root.rglob('*/router/**/*'):
        if route_file.is_file() and route_file.suffix in ('.js', '.ts', '.vue'):
            try:
                content = route_file.read_text(encoding='utf-8', errors='ignore')
                matches = re.findall(r"path:\s*['\"]([^'\"]+)['\"]", content)
                routes.extend(matches[:50])  # 最多取50条
            except (IOError, UnicodeDecodeError):
                pass

    # React Router 格式: path="/xxx" or to="/xxx"
    for route_file in project_root.rglob('*'):
        if route_file.is_file() and route_file.suffix in ('.js', '.jsx', '.ts', '.tsx'):
            try:
                content = route_file.read_text(encoding='utf-8', errors='ignore')
                matches = re.findall(r'(?:path|to)=\s*["\'`]([^"\'`]+)["\'`]', content)
                routes.extend(matches[:50])
            except (IOError, UnicodeDecodeError):
                pass

    return list(dict.fromkeys(routes))  # 去重保序


def extract_readme_excerpt(project_root: Path) -> str:
    """提取 README 摘要"""
    for readme_name in ['README.md', 'README.MD', 'readme.md', 'Readme.md', 'README.txt']:
        readme_path = project_root / readme_name
        if readme_path.exists():
            try:
                content = readme_path.read_text(encoding='utf-8', errors='ignore')
                lines = [l.strip() for l in content.split('\n') if l.strip() and not l.strip().startswith('![')]
                return '\n'.join(lines[:60])  # 前60行
            except IOError:
                pass
    return ''


def extract_feature_kw_from_routes(routes: List[str]) -> List[str]:
    """从路由路径中提取功能关键词"""
    kw = set()
    for route in routes:
        # 去掉参数和特殊字符
        clean = re.sub(r'/[:_]\w+', '', route)
        parts = [p for p in clean.split('/') if p and len(p) > 1 and not p.startswith(':')]
        for part in parts:
            if re.match(r'^[a-zA-Z][a-zA-Z0-9_-]+$', part):
                kw.add(part)
    return sorted(kw)[:40]


def run_command_candidates(package: Optional[dict]) -> List[str]:
    """提取可能的前端启动命令"""
    if not package:
        return []
    scripts = package.get('scripts', {})
    candidates = []
    for name in ['dev', 'start', 'serve', 'develop', 'development']:
        if name in scripts:
            candidates.append(f"npm run {name}")
    return candidates


def analyze(project_root: Path) -> dict:
    """核心分析函数"""
    result = {
        "schema_version": "1.0",
        "project_root": str(project_root.resolve()),
    }

    # 文件扫描
    file_categories = Counter()
    ext_counts = Counter()
    total_lines = 0
    total_files = 0
    max_depth = 10  # 限制扫描深度

    for file_path in project_root.rglob('*'):
        # 深度限制
        depth = len(file_path.relative_to(project_root).parts)
        if depth > max_depth:
            continue

        if not file_path.is_file():
            continue
        if should_exclude_dir(file_path.parent):
            continue
        if is_config_file(file_path.name):
            continue

        if is_source_file(file_path):
            total_files += 1
            ext = file_path.suffix.lower()
            ext_counts[ext] += 1
            category = classify_file(file_path, project_root)
            file_categories[category] += 1

            try:
                line_count = sum(1 for _ in open(file_path, encoding='utf-8', errors='ignore'))
                total_lines += line_count
            except (IOError, UnicodeDecodeError):
                pass

    # 包信息
    package = load_package_json(project_root)
    project_name = ''
    if package:
        project_name = package.get('name', '')
        if not project_name:
            # 从当前目录名推测
            project_name = project_root.resolve().name

    # 框架检测
    frameworks = detect_frameworks(package, ext_counts)

    # 语言推断
    language = infer_language(ext_counts)

    # 路由提取
    routes = extract_routes(project_root)

    # README 摘要
    readme = extract_readme_excerpt(project_root)

    # 运行命令
    run_cmds = run_command_candidates(package)

    # 功能关键词
    features = extract_feature_kw_from_routes(routes)

    result.update({
        "project_name": project_name or project_root.resolve().name,
        "software_name_candidate": project_name,
        "package": {
            "name": package.get('name', '') if package else '',
            "version": package.get('version', '') if package else '',
            "scripts": list(package.get('scripts', {}).keys()) if package else [],
        } if package else None,
        "frameworks": frameworks,
        "language": language,
        "source": {
            "total_files": total_files,
            "total_lines": total_lines,
            "extensions": dict(ext_counts.most_common(15)),
            "categories": dict(file_categories),
        },
        "routes": routes[:30],
        "readme_excerpt": readme,
        "run_command_candidates": run_cmds,
        "feature_candidates": features,
    })

    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="分析项目结构用于软著材料生成")
    parser.add_argument("--project", required=True, help="项目根目录路径")
    parser.add_argument("--out", help="输出 JSON 文件路径")
    parser.add_argument("--max-depth", type=int, default=10, help="扫描深度限制 (默认10)")
    args = parser.parse_args()

    global max_depth_limit
    max_depth_limit = args.max_depth

    project_path = Path(args.project)
    if not project_path.exists():
        print(f"[ERR] 项目路径不存在: {project_path}")
        sys.exit(1)

    print(f"[*] 正在分析项目: {project_path}")
    result = analyze(project_path)

    out_path = Path(args.out) if args.out else project_path / '软著申请资料' / 'analysis' / 'project.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

    print()
    print(f"[*] 项目分析结果：")
    print(f"   项目名称: {result['project_name']}")
    print(f"   编程语言: {result['language']}")
    print(f"   框架: {', '.join(result['frameworks'])}")
    print(f"   源码文件: {result['source']['total_files']} 个")
    print(f"   代码总行: {result['source']['total_lines']:,} 行")
    print(f"   路由数量: {len(result['routes'])} 条")
    print()
    print(f"[OK] 分析结果已保存: {out_path}")


if __name__ == "__main__":
    main()
