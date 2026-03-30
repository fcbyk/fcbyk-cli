"""参数占位符解析测试"""
import pytest
from fcbyk.core.alias import parse_arguments


class TestParseArguments:
    """测试参数解析功能"""
    
    def test_no_placeholder_auto_pass(self):
        """测试无占位符时自动透传"""
        cmd_str = "vite"
        args = ["--port", "3000"]
        result = parse_arguments(cmd_str, args)
        assert result == "vite --port 3000"
    
    def test_no_args_no_placeholder(self):
        """测试无参数无占位符"""
        cmd_str = "vite"
        args = []
        result = parse_arguments(cmd_str, args)
        assert result == "vite"
    
    def test_args_placeholder(self):
        """测试 {args} 占位符"""
        cmd_str = "jest {args}"
        args = ["src/index.test.js", "--coverage"]
        result = parse_arguments(cmd_str, args)
        assert result == "jest src/index.test.js --coverage"
    
    def test_single_index_placeholder(self):
        """测试单个索引占位符 {0}"""
        cmd_str = "eslint {0} --fix"
        args = ["src/index.js"]
        result = parse_arguments(cmd_str, args)
        assert result == "eslint src/index.js --fix"
    
    def test_multiple_index_placeholders(self):
        """测试多个索引占位符"""
        cmd_str = "cp {0} {1}"
        args = ["src/file.txt", "dest/file.txt"]
        result = parse_arguments(cmd_str, args)
        assert result == "cp src/file.txt dest/file.txt"
    
    def test_non_sequential_placeholders(self):
        """测试非连续索引占位符（关键测试）"""
        cmd_str = "echo {2} {0}"
        args = ["first", "second", "third"]
        result = parse_arguments(cmd_str, args)
        assert result == "echo third first"
    
    def test_only_second_placeholder(self):
        """测试只使用 {1} 而不使用 {0}"""
        cmd_str = "command --option {1}"
        args = ["ignored", "value"]
        result = parse_arguments(cmd_str, args)
        assert result == "command --option value"
    
    def test_reverse_order_placeholders(self):
        """测试逆序占位符"""
        cmd_str = "echo {2} {1} {0}"
        args = ["first", "second", "third"]
        result = parse_arguments(cmd_str, args)
        assert result == "echo third second first"
    
    def test_duplicate_placeholders(self):
        """测试重复占位符"""
        cmd_str = "echo {0} {0} {0}"
        args = ["hello"]
        result = parse_arguments(cmd_str, args)
        assert result == "echo hello hello hello"
    
    def test_missing_argument_error(self):
        """测试参数不足时报错"""
        cmd_str = "echo {0} {1} {2}"
        args = ["only_one"]
        with pytest.raises(ValueError, match=r"Missing argument for placeholder \{1\}"):
            parse_arguments(cmd_str, args)
    
    def test_missing_higher_index_error(self):
        """测试高索引参数缺失时报错"""
        cmd_str = "echo {5}"
        args = ["one", "two", "three"]
        with pytest.raises(ValueError, match=r"Missing argument for placeholder \{5\}"):
            parse_arguments(cmd_str, args)
    
    def test_mixed_args_and_index(self):
        """测试混合使用 args 和索引（args 优先）"""
        # 这种情况 {args} 会被处理，索引占位符不会被替换
        cmd_str = "echo {args} and {0}"
        args = ["a", "b"]
        result = parse_arguments(cmd_str, args)
        # {args} 被替换，{0} 保持不变（因为代码先检查 {args}）
        assert result == "echo a b and {0}"
    
    def test_complex_command_with_cwd(self):
        """测试复杂命令带工作目录"""
        cmd_str = "pnpm run build --mode {1} --env {0}"
        args = ["production", "staging"]
        result = parse_arguments(cmd_str, args)
        assert result == "pnpm run build --mode staging --env production"
    
    def test_large_index_with_enough_args(self):
        """测试大索引但有足够参数"""
        cmd_str = "echo {9}"
        args = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "ninth"]
        result = parse_arguments(cmd_str, args)
        assert result == "echo ninth"
    
    def test_placeholder_with_special_chars(self):
        """测试占位符包含特殊字符"""
        cmd_str = "echo {0}"
        args = ["hello world"]
        result = parse_arguments(cmd_str, args)
        assert result == "echo hello world"
    
    def test_multiple_same_placeholder(self):
        """测试同一个占位符出现多次"""
        cmd_str = "git log {0}..{0}"
        args = ["HEAD~1"]
        result = parse_arguments(cmd_str, args)
        assert result == "git log HEAD~1..HEAD~1"
