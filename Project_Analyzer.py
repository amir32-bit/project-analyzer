#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Analyzer - ابزار تحلیل خودکار پروژه
خلاصه‌نویسی برای AI بدون دخالت دستی
"""

import os
import json
from pathlib import Path
from collections import defaultdict
import ast
import re

class ProjectAnalyzer:
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.analysis = {
            'project_name': self.project_path.name,
            'structure': {},
            'files_info': defaultdict(list),
            'languages': defaultdict(int),
            'dependencies': [],
            'description': '',
            'modules': [],
            'functions': [],
            'classes': [],
            'config_files': [],
            'documentation': []
        }
        
    def analyze(self):
        """شروع تحلیل پروژه"""
        print(f"🔍 تحلیل پروژه: {self.project_path}")
        
        self.scan_directory()
        self.extract_dependencies()
        self.analyze_python_files()
        self.find_config_files()
        self.find_documentation()
        self.extract_readme()
        
        return self.analysis
    
    def scan_directory(self):
        """بررسی ساختار دایرکتوری"""
        structure = defaultdict(list)
        
        ignore_dirs = {'.git', '__pycache__', '.env', 'node_modules', 
                      '.venv', 'venv', '.pytest_cache', '.egg-info'}
        ignore_extensions = {'.pyc', '.pyo', '.so', '.o', '.a'}
        
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            level = root.replace(str(self.project_path), '').count(os.sep)
            relative_path = os.path.relpath(root, self.project_path)
            
            for file in files:
                if not any(file.endswith(ext) for ext in ignore_extensions):
                    ext = Path(file).suffix or 'no_extension'
                    structure[ext].append(os.path.join(relative_path, file))
                    self.analysis['languages'][ext] += 1
        
        self.analysis['structure'] = dict(structure)
    
    def extract_dependencies(self):
        """استخراج وابستگی‌ها"""
        dependencies = []
        
        req_file = self.project_path / 'requirements.txt'
        if req_file.exists():
            with open(req_file, 'r', encoding='utf-8') as f:
                dependencies.extend([line.strip() for line in f if line.strip()])
        
        setup_file = self.project_path / 'setup.py'
        if setup_file.exists():
            with open(setup_file, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if match:
                    deps = re.findall(r'["\']([^"\']+)["\']', match.group(1))
                    dependencies.extend(deps)
        
        pyproject = self.project_path / 'pyproject.toml'
        if pyproject.exists():
            with open(pyproject, 'r', encoding='utf-8') as f:
                content = f.read()
                deps = re.findall(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if deps:
                    packages = re.findall(r'["\']([^"\']+)["\']', deps[0])
                    dependencies.extend(packages)
        
        self.analysis['dependencies'] = list(set(dependencies))
    
    def analyze_python_files(self):
        """تحلیل فایل‌های پایتون"""
        python_files = self.analysis['structure'].get('.py', [])
        
        for file_path in python_files:
            full_path = self.project_path / file_path
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                try:
                    tree = ast.parse(content)
                    self.extract_from_ast(tree, file_path)
                except:
                    pass
                
                docstring = self.extract_file_docstring(content)
                if docstring:
                    self.analysis['files_info'][file_path].append(docstring)
                    
            except Exception as e:
                print(f"⚠️  خطا در خواندن {file_path}: {e}")
    
    def extract_from_ast(self, tree, file_path):
        """استخراج اطلاعات AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'file': file_path,
                    'args': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node)
                }
                self.analysis['functions'].append(func_info)
            
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'file': file_path,
                    'docstring': ast.get_docstring(node),
                    'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                }
                self.analysis['classes'].append(class_info)
    
    def extract_file_docstring(self, content):
        """استخراج docstring فایل"""
        lines = content.split('\n')
        docstring_start = None
        
        for i, line in enumerate(lines[:10]):
            if '"""' in line or "'''" in line:
                docstring_start = i
                break
        
        if docstring_start is not None:
            docstring_lines = []
            for line in lines[docstring_start:docstring_start+10]:
                docstring_lines.append(line)
                if docstring_lines[0] != line and ('"""' in line or "'''" in line):
                    break
            
            return ' '.join(docstring_lines).strip()
        
        return None
    
    def find_config_files(self):
        """پیدا کردن فایل‌های تنظیم"""
        config_patterns = [
            'setup.py', 'setup.cfg', 'pyproject.toml',
            'config.py', 'settings.py', '.env.example',
            'docker-compose.yml', 'Dockerfile', 'tox.ini',
            'pytest.ini', '.github', '.gitlab-ci.yml'
        ]
        
        for pattern in config_patterns:
            config_path = self.project_path / pattern
            if config_path.exists():
                self.analysis['config_files'].append(pattern)
    
    def find_documentation(self):
        """پیدا کردن فایل‌های مستندات"""
        doc_patterns = [
            'README.md', 'README.rst', 'CONTRIBUTING.md',
            'CHANGELOG.md', 'LICENSE', 'docs'
        ]
        
        for pattern in doc_patterns:
            doc_path = self.project_path / pattern
            if doc_path.exists():
                self.analysis['documentation'].append(pattern)
    
    def extract_readme(self):
        """استخراج محتوای README"""
        readme_files = ['README.md', 'README.rst', 'README.txt']
        
        for readme in readme_files:
            readme_path = self.project_path / readme
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.analysis['description'] = content[:500]
                    break
                except Exception as e:
                    print(f"⚠️  خطا در خواندن README: {e}")
    
    def generate_prompt(self):
        """تولید prompt برای AI"""
        prompt = f"""# تحلیل پروژه: {self.analysis['project_name']}

## اطلاعات کلی
- **نام پروژه:** {self.analysis['project_name']}
- **مسیر:** {self.project_path}

## ساختار پروژه
"""
        
        if self.analysis['structure']:
            for ext, files in sorted(self.analysis['structure'].items()):
                prompt += f"\n### فایل‌های {ext} ({len(files)} عدد)\n"
                for file in sorted(files)[:10]:
                    prompt += f"- {file}\n"
                if len(files) > 10:
                    prompt += f"- ... و {len(files) - 10} فایل دیگر\n"
        
        if self.analysis['languages']:
            prompt += "\n## زبان‌های استفاده شده\n"
            for lang, count in sorted(self.analysis['languages'].items(), 
                                     key=lambda x: x[1], reverse=True):
                prompt += f"- {lang}: {count} فایل\n"
        
        if self.analysis['dependencies']:
            prompt += "\n## وابستگی‌های اصلی\n"
            for dep in sorted(self.analysis['dependencies'])[:20]:
                prompt += f"- {dep}\n"
            if len(self.analysis['dependencies']) > 20:
                prompt += f"- ... و {len(self.analysis['dependencies']) - 20} وابستگی دیگر\n"
        
        if self.analysis['classes']:
            prompt += "\n## کلاس‌های اصلی\n"
            for cls in self.analysis['classes'][:15]:
                prompt += f"- **{cls['name']}** ({cls['file']})\n"
                if cls['docstring']:
                    prompt += f"  {cls['docstring'][:100]}\n"
                if cls['methods']:
                    prompt += f"  متدها: {', '.join(cls['methods'][:5])}\n"
        
        if self.analysis['functions']:
            prompt += "\n## توابع اصلی\n"
            for func in self.analysis['functions'][:20]:
                params = ', '.join(func['args']) if func['args'] else 'بدون پارامتر'
                prompt += f"- **{func['name']}** ({params}) - {func['file']}\n"
        
        if self.analysis['config_files']:
            prompt += "\n## فایل‌های تنظیم\n"
            for config in self.analysis['config_files']:
                prompt += f"- {config}\n"
        
        if self.analysis['documentation']:
            prompt += "\n## مستندات\n"
            for doc in self.analysis['documentation']:
                prompt += f"- {doc}\n"
        
        if self.analysis['description']:
            prompt += "\n## توضیحات اولیه (از README)\n"
            prompt += f"{self.analysis['description']}\n"
        
        prompt += "\n---\n## درخواست\n"
        prompt += """لطفا این پروژه را تحلیل کرده و موارد زیر را ارائه دهید:

1. **خلاصه کلی:** هدف و عملکرد اصلی پروژه
2. **معماری:** ساختار و طراحی پروژه
3. **کارکردهای اصلی:** بخش‌های مهم و وظایف آنها
4. **وابستگی‌ها:** نقش کتابخانه‌های اصلی
5. **نقاط قوت:** بخش‌های خوب پروژه
6. **بهبودهای پیشنهادی:** مناطقی که می‌توان بهتر کرد
7. **توصیه‌های فنی:** پیشنهادات برای بهتر شدن کد
8. **مراحل بعدی:** گام‌های توصیه شده برای توسعه
"""
        
        return prompt
    
    def save_prompt(self, output_file=None):
        """ذخیره prompt در فایل"""
        if output_file is None:
            output_file = self.project_path / 'project_prompt.md'
        
        prompt = self.generate_prompt()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        print(f"✅ Prompt ذخیره شد: {output_file}")
        return output_file
    
    def save_analysis_json(self, output_file=None):
        """ذخیره تحلیل به‌صورت JSON"""
        if output_file is None:
            output_file = self.project_path / 'project_analysis.json'
        
        analysis_dict = {
            'project_name': self.analysis['project_name'],
            'structure': dict(self.analysis['structure']),
            'languages': dict(self.analysis['languages']),
            'dependencies': self.analysis['dependencies'],
            'classes': self.analysis['classes'],
            'functions': self.analysis['functions'][:20],
            'config_files': self.analysis['config_files'],
            'documentation': self.analysis['documentation'],
            'description': self.analysis['description']
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_dict, f, ensure_ascii=False, indent=2)
        
        print(f"✅ تحلیل JSON ذخیره شد: {output_file}")
        return output_file
    
    def print_summary(self):
        """نمایش خلاصه تحلیل"""
        print("\n" + "="*60)
        print(f"📊 خلاصه تحلیل پروژه: {self.analysis['project_name']}")
        print("="*60)
        
        print(f"\n📁 تعداد فایل‌ها: {sum(self.analysis['languages'].values())}")
        print(f"🔤 زبان‌های استفاده شده: {len(self.analysis['languages'])}")
        print(f"📦 وابستگی‌ها: {len(self.analysis['dependencies'])}")
        print(f"🏗️  کلاس‌ها: {len(self.analysis['classes'])}")
        print(f"⚙️  توابع: {len(self.analysis['functions'])}")
        print(f"⚙️  فایل‌های تنظیم: {len(self.analysis['config_files'])}")
        
        print("\n" + "="*60)


def main():
    """نقطه ورود اصلی"""
    import sys
    
    if len(sys.argv) < 2:
        print("📖 استفاده: python file.py <مسیر_پروژه>")
        print("\nمثال:")
        print("  python file.py C:\\Users\\YourName\\Desktop\\MyProject")
        print("  python file.py /home/user/projects/myproject")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    if not os.path.exists(project_path):
        print(f"❌ خطا: مسیر وجود ندارد: {project_path}")
        sys.exit(1)
    
    analyzer = ProjectAnalyzer(project_path)
    analyzer.analyze()
    analyzer.print_summary()
    
    analyzer.save_prompt()
    analyzer.save_analysis_json()
    
    print("\n🎉 تحلیل پروژه به پایان رسید!")
    print("📄 فایل‌های خروجی:")
    print(f"  - project_prompt.md (برای استفاده با AI)")
    print(f"  - project_analysis.json (داده‌های تحلیلی)")


if __name__ == '__main__':
    main()
