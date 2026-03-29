"""Alias 分组功能测试"""
import pytest
from fcbyk.commands.alias.cli import resolve_nested_alias, collect_all_alias_paths


class TestResolveNestedAlias:
    """测试嵌套别名解析功能"""
    
    def test_simple_string_alias(self):
        """测试简单字符串别名"""
        aliases = {
            "test": "pytest -q"
        }
        cmd_str, cwd = resolve_nested_alias(aliases, "test")
        assert cmd_str == "pytest -q"
        assert cwd is None
    
    def test_object_alias_without_cwd(self):
        """测试对象形式别名（无 cwd）"""
        aliases = {
            "build": {
                "cmd": "python -m build"
            }
        }
        cmd_str, cwd = resolve_nested_alias(aliases, "build")
        assert cmd_str == "python -m build"
        assert cwd is None
    
    def test_object_alias_with_cwd(self):
        """测试对象形式别名（带 cwd）"""
        aliases = {
            "frontend-build": {
                "cmd": "pnpm run build",
                "cwd": "/path/to/frontend"
            }
        }
        cmd_str, cwd = resolve_nested_alias(aliases, "frontend-build")
        assert cmd_str == "pnpm run build"
        assert cwd == "/path/to/frontend"
    
    def test_single_level_group(self):
        """测试单层分组"""
        aliases = {
            "dev": {
                "test": "pytest"
            }
        }
        cmd_str, cwd = resolve_nested_alias(aliases, "dev.test")
        assert cmd_str == "pytest"
        assert cwd is None
    
    def test_multi_level_group(self):
        """测试多层分组"""
        aliases = {
            "开发": {
                "构建": {
                    "前端": {
                        "cmd": "pnpm run build",
                        "cwd": "./web-ui"
                    }
                }
            }
        }
        cmd_str, cwd = resolve_nested_alias(aliases, "开发.构建.前端")
        assert cmd_str == "pnpm run build"
        assert cwd == "./web-ui"
    
    def test_mixed_aliases(self):
        """测试混合别名（简单 + 对象 + 分组）"""
        aliases = {
            "simple": "echo hello",
            "group": {
                "nested": {
                    "cmd": "ls -la"
                }
            },
            "another": {
                "cmd": "pwd",
                "cwd": "/tmp"
            }
        }
        
        # 测试简单别名
        cmd_str, cwd = resolve_nested_alias(aliases, "simple")
        assert cmd_str == "echo hello"
        assert cwd is None
        
        # 测试嵌套分组
        cmd_str, cwd = resolve_nested_alias(aliases, "group.nested")
        assert cmd_str == "ls -la"
        assert cwd is None
        
        # 测试对象别名
        cmd_str, cwd = resolve_nested_alias(aliases, "another")
        assert cmd_str == "pwd"
        assert cwd == "/tmp"
    
    def test_nonexistent_alias(self):
        """测试不存在的别名"""
        aliases = {
            "test": "pytest"
        }
        cmd_str, cwd = resolve_nested_alias(aliases, "nonexistent")
        assert cmd_str is None
        assert cwd is None
    
    def test_incomplete_path(self):
        """测试不完整的路径（中间节点）"""
        aliases = {
            "dev": {
                "test": "pytest"
            }
        }
        cmd_str, cwd = resolve_nested_alias(aliases, "dev")
        assert cmd_str is None
        assert cwd is None
    
    def test_invalid_path_type(self):
        """测试无效路径类型（字符串值后面还有路径）"""
        aliases = {
            "dev": {
                "test": "pytest"
            }
        }
        # 尝试访问 dev.test.extra，但 dev.test 是字符串
        cmd_str, cwd = resolve_nested_alias(aliases, "dev.test.extra")
        assert cmd_str is None
        assert cwd is None
    
    def test_empty_aliases(self):
        """测试空字典"""
        aliases = {}
        cmd_str, cwd = resolve_nested_alias(aliases, "test")
        assert cmd_str is None
        assert cwd is None


class TestCollectAllAliasPaths:
    """测试收集所有别名路径功能"""
    
    def test_simple_aliases(self):
        """测试简单别名列表"""
        aliases = {
            "test": "pytest",
            "build": "python -m build"
        }
        paths = collect_all_alias_paths(aliases)
        assert sorted(paths) == ["build", "test"]
    
    def test_nested_groups(self):
        """测试嵌套分组"""
        aliases = {
            "开发": {
                "测试": "pytest",
                "构建": {
                    "前端": "pnpm build",
                    "后端": "python build"
                }
            }
        }
        paths = collect_all_alias_paths(aliases)
        expected = [
            "开发.测试",
            "开发.构建.前端",
            "开发.构建.后端"
        ]
        assert sorted(paths) == sorted(expected)
    
    def test_mixed_structure(self):
        """测试混合结构"""
        aliases = {
            "simple": "echo",
            "group": {
                "alias": "ls",
                "subgroup": {
                    "deep": "pwd"
                }
            }
        }
        paths = collect_all_alias_paths(aliases)
        expected = ["simple", "group.alias", "group.subgroup.deep"]
        assert sorted(paths) == sorted(expected)
    
    def test_empty_dict(self):
        """测试空字典"""
        aliases = {}
        paths = collect_all_alias_paths(aliases)
        assert paths == []
    
    def test_object_with_cmd(self):
        """测试带 cmd 的对象"""
        aliases = {
            "build": {
                "cmd": "python -m build",
                "cwd": "/path"
            }
        }
        paths = collect_all_alias_paths(aliases)
        assert paths == ["build"]
