#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Analyzer - Automatic Project Analysis Tool
Summary generation for AI without manual intervention
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
        """Start project analysis"""
        print(f"🔍 Analyzing project: {self.project_path}")
        
        self.scan_directory()
        self.extract_dependencies()
        self.analyze_python_files()
        self.find_config_files()
        self.find_documentation()
        self.extract_readme()
        
        return self.analysis
    
    def scan_directory(self):
        """Scan directory structure"""
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
        """Extract dependencies"""
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
        """Analyze Python files"""
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
                print(f"⚠️  Error reading {file_path}: {e}")
    
    def extract_from_ast(self, tree, file_path):
        """Extract information from AST"""
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
        """Extract file docstring"""
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
        """Find configuration files"""
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
        """Find documentation files"""
        doc_patterns = [
            'README.md', 'README.rst', 'CONTRIBUTING.md',
            'CHANGELOG.md', 'LICENSE', 'docs'
        ]
        
        for pattern in doc_patterns:
            doc_path = self.project_path / pattern
            if doc_path.exists():
                self.analysis['documentation'].append(pattern)
    
    def extract_readme(self):
        """Extract README content"""
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
                    print(f"⚠️  Error reading README: {e}")
    
    def generate_prompt(self):
        """Generate prompt for AI"""
        prompt = f"""# Project Analysis: {self.analysis['project_name']}

## General Information
- **Project Name:** {self.analysis['project_name']}
- **Path:** {self.project_path}

## Project Structure
"""
        
        if self.analysis['structure']:
            for ext, files in sorted(self.analysis['structure'].items()):
                prompt += f"\n### Files {ext} ({len(files)} total)\n"
                for file in sorted(files)[:10]:
                    prompt += f"- {file}\n"
                if len(files) > 10:
                    prompt += f"- ... and {len(files) - 10} more files\n"
        
        if self.analysis['languages']:
            prompt += "\n## Programming Languages Used\n"
            for lang, count in sorted(self.analysis['languages'].items(), 
                                     key=lambda x: x[1], reverse=True):
                prompt += f"- {lang}: {count} files\n"
        
        if self.analysis['dependencies']:
            prompt += "\n## Main Dependencies\n"
            for dep in sorted(self.analysis['dependencies'])[:20]:
                prompt += f"- {dep}\n"
            if len(self.analysis['dependencies']) > 20:
                prompt += f"- ... and {len(self.analysis['dependencies']) - 20} more dependencies\n"
        
        if self.analysis['classes']:
            prompt += "\n## Main Classes\n"
            for cls in self.analysis['classes'][:15]:
                prompt += f"- **{cls['name']}** ({cls['file']})\n"
                if cls['docstring']:
                    prompt += f"  {cls['docstring'][:100]}\n"
                if cls['methods']:
                    prompt += f"  Methods: {', '.join(cls['methods'][:5])}\n"
        
        if self.analysis['functions']:
            prompt += "\n## Main Functions\n"
            for func in self.analysis['functions'][:20]:
                params = ', '.join(func['args']) if func['args'] else 'no parameters'
                prompt += f"- **{func['name']}** ({params}) - {func['file']}\n"
        
        if self.analysis['config_files']:
            prompt += "\n## Configuration Files\n"
            for config in self.analysis['config_files']:
                prompt += f"- {config}\n"
        
        if self.analysis['documentation']:
            prompt += "\n## Documentation\n"
            for doc in self.analysis['documentation']:
                prompt += f"- {doc}\n"
        
        if self.analysis['description']:
            prompt += "\n## Initial Description (from README)\n"
            prompt += f"{self.analysis['description']}\n"
        
        prompt += "\n---\n## Request\n"
        prompt += """Please analyze this project and provide the following:

1. **Overall Summary:** Project purpose and main functionality
2. **Architecture:** Project structure and design
3. **Main Features:** Important sections and their responsibilities
4. **Dependencies:** Role of main libraries
5. **Strengths:** Well-designed parts of the project
6. **Suggested Improvements:** Areas that could be enhanced
7. **Technical Recommendations:** Suggestions for better code quality
8. **Next Steps:** Recommended actions for development
"""
        
        return prompt
    
    def save_prompt(self, output_file=None):
        """Save prompt to file"""
        if output_file is None:
            output_file = self.project_path / 'project_prompt.md'
        
        prompt = self.generate_prompt()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        print(f"✅ Prompt saved: {output_file}")
        return output_file
    
    def save_analysis_json(self, output_file=None):
        """Save analysis as JSON"""
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
        
        print(f"✅ JSON analysis saved: {output_file}")
        return output_file
    
    def print_summary(self):
        """Display analysis summary"""
        print("\n" + "="*60)
        print(f"📊 Project Analysis Summary: {self.analysis['project_name']}")
        print("="*60)
        
        print(f"\n📁 Total Files: {sum(self.analysis['languages'].values())}")
        print(f"🔤 Programming Languages: {len(self.analysis['languages'])}")
        print(f"📦 Dependencies: {len(self.analysis['dependencies'])}")
        print(f"🏗️  Classes: {len(self.analysis['classes'])}")
        print(f"⚙️  Functions: {len(self.analysis['functions'])}")
        print(f"⚙️  Configuration Files: {len(self.analysis['config_files'])}")
        
        print("\n" + "="*60)


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("📖 Usage: python file.py <project_path>")
        print("\nExamples:")
        print("  python file.py C:\\Users\\YourName\\Desktop\\MyProject")
        print("  python file.py /home/user/projects/myproject")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    if not os.path.exists(project_path):
        print(f"❌ Error: Path does not exist: {project_path}")
        sys.exit(1)
    
    analyzer = ProjectAnalyzer(project_path)
    analyzer.analyze()
    analyzer.print_summary()
    
    analyzer.save_prompt()
    analyzer.save_analysis_json()
    
    print("\n🎉 Project analysis complete!")
    print("📄 Output files:")
    print(f"  - project_prompt.md (for use with AI)")
    print(f"  - project_analysis.json (analysis data)")


if __name__ == '__main__':
    main()
