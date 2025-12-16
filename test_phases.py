#!/usr/bin/env python3
"""
Comprehensive test suite for Phase 1 and Phase 2 implementations.
Tests all modules, commands, and integrations before Phase 3 development.
"""

import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def print_test_header(test_name: str):
    """Print a formatted test header"""
    print("\n" + "="*70)
    print(f"  {test_name}")
    print("="*70)

def print_result(success: bool, message: str):
    """Print test result"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status}: {message}")

# ============================================================================
# PHASE 1 TESTS: Configuration, Logging, Utilities
# ============================================================================

def test_phase1_constants():
    """Test constants module import and values"""
    print_test_header("PHASE 1 TEST: Constants Module")
    
    try:
        from constants import (
            GREETING_WORDS, QUESTION_MARKERS, HELP_KEYWORDS,
            SPECS_KEYWORDS, HYPE_TRIGGERS, STATS_TRIGGERS,
            COMMUNITY_TRIGGERS, VALORANT_AGENTS
        )
        
        print_result(True, "All constants imported successfully")
        print(f"  - Greeting words: {len(GREETING_WORDS)} items")
        print(f"  - Valorant agents: {len(VALORANT_AGENTS)} items")
        print(f"  - Hype triggers: {len(HYPE_TRIGGERS)} items")
        
        # Verify key constants exist
        assert len(GREETING_WORDS) > 0, "Greeting words should not be empty"
        assert len(VALORANT_AGENTS) > 0, "Valorant agents should not be empty"
        
        print_result(True, "Constants module validation complete")
        return True
        
    except Exception as e:
        print_result(False, f"Constants module error: {e}")
        return False

def test_phase1_logger():
    """Test logging system"""
    print_test_header("PHASE 1 TEST: Logging System")
    
    try:
        from logger import get_logger
        
        # Create a test logger
        logger = get_logger("test_module")
        print_result(True, "Logger created successfully")
        
        # Test different log levels
        logger.debug("Debug message - testing logging system")
        logger.info("Info message - testing logging system")
        logger.warning("Warning message - testing logging system")
        
        print_result(True, "All log levels working")
        
        # Check if log file was created
        log_dir = Path(__file__).parent / "logs"
        if log_dir.exists() and any(log_dir.glob("bot_*.log")):
            print_result(True, f"Log files created in {log_dir}")
        else:
            print_result(False, f"Log directory not found or empty: {log_dir}")
            return False
        
        print_result(True, "Logging system validation complete")
        return True
        
    except Exception as e:
        print_result(False, f"Logger error: {e}")
        return False

def test_phase1_file_utils():
    """Test file utilities"""
    print_test_header("PHASE 1 TEST: File Utilities")
    
    try:
        from utils.file_utils import (
            save_stats_to_file,
            load_processed_messages,
            save_message_id
        )
        
        print_result(True, "File utilities imported successfully")
        
        # Test save_stats_to_file
        test_file = Path(__file__).parent / "app" / "data" / "test_stats.txt"
        save_stats_to_file("Test data content", test_file)
        
        if test_file.exists():
            print_result(True, f"save_stats_to_file created file: {test_file}")
            content = test_file.read_text()
            if content == "Test data content":
                print_result(True, "File content matches")
            else:
                print_result(False, f"File content mismatch: {content}")
            test_file.unlink()  # Clean up
        else:
            print_result(False, "save_stats_to_file did not create file")
            return False
        
        # Test load_processed_messages
        messages = load_processed_messages()
        print_result(True, f"load_processed_messages returned {len(messages)} messages")
        
        # Test save_message_id
        test_id = "test_message_id_12345"
        save_message_id(test_id)
        messages_after = load_processed_messages()
        if test_id in messages_after:
            print_result(True, "save_message_id successfully saved ID")
        else:
            print_result(False, "save_message_id did not save ID")
            return False
        
        print_result(True, "File utilities validation complete")
        return True
        
    except Exception as e:
        print_result(False, f"File utilities error: {e}")
        return False

def test_phase1_config_validator():
    """Test configuration validator"""
    print_test_header("PHASE 1 TEST: Configuration Validator")
    
    try:
        from config_validator import (
            validate_api_keys,
            validate_valorant_id,
            validate_file_structure
        )
        
        print_result(True, "Config validator imported successfully")
        
        # Test API key validation
        has_keys = validate_api_keys()
        print_result(has_keys, f"API keys validation: {'Found' if has_keys else 'Not found (OK for testing)'}")
        
        # Test Valorant ID validation
        valid_ids = [
            ("Player#NA1", True),
            ("test#123", True),
            ("invalidformat", False),
            ("no#hash#multiple", False)
        ]
        
        all_correct = True
        for val_id, expected in valid_ids:
            result = validate_valorant_id(val_id)
            if result == expected:
                print_result(True, f"Valorant ID '{val_id}': {result} (expected {expected})")
            else:
                print_result(False, f"Valorant ID '{val_id}': {result} (expected {expected})")
                all_correct = False
        
        if not all_correct:
            return False
        
        # Test file structure validation
        validate_file_structure()
        print_result(True, "File structure validation complete")
        
        print_result(True, "Configuration validator validation complete")
        return True
        
    except Exception as e:
        print_result(False, f"Config validator error: {e}")
        return False

# ============================================================================
# PHASE 2 TESTS: Commands, Chat Features
# ============================================================================

def test_phase2_command_base():
    """Test command base classes"""
    print_test_header("PHASE 2 TEST: Command Base Classes")
    
    try:
        from commands.command import BaseCommand, CommandContext
        
        print_result(True, "BaseCommand and CommandContext imported")
        
        # Test CommandContext creation
        context = CommandContext(
            author="TestUser",
            message="!test arg1 arg2"
        )
        
        print_result(True, f"CommandContext created: author={context.author}")
        print(f"  - Message: {context.message}")
        print(f"  - Timestamp: {context.timestamp}")
        
        # Create a simple test command
        class TestCommand(BaseCommand):
            name = "test"
            description = "Test command"
            usage = "!test"
            
            async def execute(self, context: CommandContext):
                return f"Test executed for {context.author}"
        
        test_cmd = TestCommand()
        print_result(True, f"Test command created: {test_cmd.name}")
        
        # Test parse_args
        args = test_cmd.parse_args("!test arg1 arg2")
        print_result(len(args) == 2, f"parse_args returned {len(args)} args: {args}")
        
        print_result(True, "Command base classes validation complete")
        return True
        
    except Exception as e:
        print_result(False, f"Command base classes error: {e}")
        return False

def test_phase2_command_parser():
    """Test command parser"""
    print_test_header("PHASE 2 TEST: Command Parser")
    
    try:
        from commands.parser import CommandParser
        from commands.command import BaseCommand, CommandContext
        
        print_result(True, "CommandParser imported")
        
        # Create parser
        parser = CommandParser()
        print_result(True, "CommandParser instantiated")
        
        # Create and register test command
        class PingCommand(BaseCommand):
            name = "ping"
            aliases = ["p"]
            description = "Test ping"
            usage = "!ping"
            
            async def execute(self, context: CommandContext):
                return "Pong!"
        
        ping_cmd = PingCommand()
        parser.register(ping_cmd)
        print_result(True, f"Registered command: {ping_cmd.name} with aliases {ping_cmd.aliases}")
        
        # Test command lookup
        found_cmd = parser.get_command("ping")
        print_result(found_cmd is not None, "Found command by name")
        
        found_alias = parser.get_command("p")
        print_result(found_alias is not None, "Found command by alias")
        
        # Test is_command
        is_cmd = parser.is_command("!ping test")
        print_result(is_cmd, "is_command detected command format")
        
        not_cmd = parser.is_command("hello world")
        print_result(not not_cmd, "is_command rejected non-command format")
        
        print_result(True, "Command parser validation complete")
        return True
        
    except Exception as e:
        print_result(False, f"Command parser error: {e}")
        return False

def test_phase2_builtin_commands():
    """Test built-in commands"""
    print_test_header("PHASE 2 TEST: Built-in Commands")
    
    try:
        from commands.builtins import (
            HelpCommand, PingCommand, UptimeCommand,
            SocialsCommand, StatusCommand
        )
        from commands.command import CommandContext
        import asyncio
        
        print_result(True, "All built-in commands imported")
        
        # Test each command
        commands = [
            (HelpCommand(), "!help"),
            (PingCommand(), "!ping"),
            (UptimeCommand(), "!uptime"),
            (SocialsCommand(), "!socials"),
            (StatusCommand(), "!status"),
        ]
        
        async def test_commands():
            for cmd, msg in commands:
                context = CommandContext(author="TestUser", message=msg)
                response = await cmd.execute(context)
                
                if response:
                    print_result(True, f"{cmd.name}: {response[:60]}...")
                else:
                    print_result(False, f"{cmd.name}: No response")
                    return False
            return True
        
        success = asyncio.run(test_commands())
        if not success:
            return False
        
        print_result(True, "Built-in commands validation complete")
        return True
        
    except Exception as e:
        print_result(False, f"Built-in commands error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase2_valorant_commands():
    """Test Valorant commands"""
    print_test_header("PHASE 2 TEST: Valorant Commands")
    
    try:
        from commands.valorant import (
            ValorantStatsCommand, ValorantAgentCommand, ValorantMapCommand
        )
        from commands.command import CommandContext
        import asyncio
        
        print_result(True, "All Valorant commands imported")
        
        # Test each command
        commands = [
            (ValorantStatsCommand(), "!val Player#NA1"),
            (ValorantAgentCommand(), "!agent jett"),
            (ValorantMapCommand(), "!map ascent"),
        ]
        
        async def test_commands():
            for cmd, msg in commands:
                context = CommandContext(author="TestUser", message=msg)
                response = await cmd.execute(context)
                
                if response:
                    print_result(True, f"{cmd.name}: {response[:60]}...")
                else:
                    print_result(False, f"{cmd.name}: No response")
                    return False
            return True
        
        success = asyncio.run(test_commands())
        if not success:
            return False
        
        print_result(True, "Valorant commands validation complete")
        return True
        
    except Exception as e:
        print_result(False, f"Valorant commands error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase2_chat_features():
    """Test chat features (rate limiter, spam detector, engagement tracker)"""
    print_test_header("PHASE 2 TEST: Chat Features")
    
    try:
        from chat_features import (
            RateLimiter, SpamDetector, UserEngagementTracker
        )
        import time
        
        print_result(True, "Chat features imported")
        
        # Test RateLimiter
        rate_limiter = RateLimiter(calls_per_period=2, period_seconds=3)
        print_result(True, "RateLimiter created (max 2 requests per 3 seconds)")
        
        # First request should be allowed
        allowed1 = rate_limiter.is_allowed("user1")
        print_result(allowed1, "Request 1: Allowed")
        
        # Second request should be allowed
        allowed2 = rate_limiter.is_allowed("user1")
        print_result(allowed2, "Request 2: Allowed")
        
        # Third request should be blocked
        allowed3 = rate_limiter.is_allowed("user1")
        print_result(not allowed3, "Request 3: Blocked (rate limit)")
        
        # Test SpamDetector
        spam_detector = SpamDetector()
        print_result(True, "SpamDetector created")
        
        # Test spam detection with known spam pattern
        spam1 = spam_detector.is_spam("user2", "check out my channel")
        print_result(spam1, "Message with spam pattern: Detected as spam")
        
        # Test non-spam message
        spam2 = spam_detector.is_spam("user2", "hello world")
        print_result(not spam2, "Normal message: Not spam")
        
        # Test UserEngagementTracker
        tracker = UserEngagementTracker()
        print_result(True, "UserEngagementTracker created")
        
        # Track messages
        tracker.record_message("user3")
        tracker.record_message("user3")
        
        stats = tracker.get_user_stats("user3")
        print_result(
            stats['messages'] == 2,
            f"User stats: {stats['messages']} messages"
        )
        
        # Get top users
        tracker.record_message("user4")
        top_users = tracker.get_top_users(limit=2)
        print_result(
            len(top_users) > 0,
            f"Top users: {top_users}"
        )
        
        print_result(True, "Chat features validation complete")
        return True
        
    except Exception as e:
        print_result(False, f"Chat features error: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_integration_chat_bridge():
    """Test chat bridge integration"""
    print_test_header("INTEGRATION TEST: Chat Bridge")
    
    try:
        # Check if chat_bridge imports correctly with all dependencies
        from youtube_integration.chat_bridge import YouTubeChatBridge
        
        print_result(True, "YouTubeChatBridge imported successfully")
        print("  - All Phase 1 and Phase 2 imports integrated")
        
        # Note: We can't fully instantiate without YouTube API setup
        print_result(True, "Chat bridge integration check complete")
        print("  ⚠ Note: Full instantiation requires YouTube API credentials")
        
        return True
        
    except Exception as e:
        print_result(False, f"Chat bridge integration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_main_script():
    """Test main script imports"""
    print_test_header("INTEGRATION TEST: Main Script")
    
    try:
        # Test if main script can import all dependencies
        # Note: We're just checking imports, not running the bot
        import sys
        import importlib.util
        
        main_script = Path(__file__).parent / "app" / "run_youtube_bot.py"
        
        if not main_script.exists():
            print_result(False, f"Main script not found: {main_script}")
            return False
        
        # Load the module spec
        spec = importlib.util.spec_from_file_location("run_youtube_bot", main_script)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            
            # Try to execute module (this will fail if imports are broken)
            try:
                spec.loader.exec_module(module)
                print_result(False, "Module executed (should have stopped before main)")
            except SystemExit:
                # Expected - script tries to run but we don't provide video_id
                print_result(True, "Main script imports successful")
            except Exception as e:
                if "video_id" in str(e).lower() or "argument" in str(e).lower():
                    print_result(True, "Main script imports successful (missing args expected)")
                else:
                    print_result(False, f"Main script error: {e}")
                    return False
        else:
            print_result(False, "Could not load main script spec")
            return False
        
        print_result(True, "Main script integration check complete")
        return True
        
    except Exception as e:
        print_result(False, f"Main script integration error: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*70)
    print("  PHASE 1 & PHASE 2 COMPREHENSIVE TEST SUITE")
    print("  Testing all implemented features before Phase 3")
    print("="*70)
    
    results = {}
    
    # Phase 1 Tests
    results['Phase 1: Constants'] = test_phase1_constants()
    results['Phase 1: Logger'] = test_phase1_logger()
    results['Phase 1: File Utils'] = test_phase1_file_utils()
    results['Phase 1: Config Validator'] = test_phase1_config_validator()
    
    # Phase 2 Tests
    results['Phase 2: Command Base'] = test_phase2_command_base()
    results['Phase 2: Command Parser'] = test_phase2_command_parser()
    results['Phase 2: Built-in Commands'] = test_phase2_builtin_commands()
    results['Phase 2: Valorant Commands'] = test_phase2_valorant_commands()
    results['Phase 2: Chat Features'] = test_phase2_chat_features()
    
    # Integration Tests
    results['Integration: Chat Bridge'] = test_integration_chat_bridge()
    results['Integration: Main Script'] = test_integration_main_script()
    
    # Summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "-"*70)
    print(f"  TOTAL: {passed}/{total} tests passed ({passed*100//total}%)")
    print("="*70)
    
    if passed == total:
        print("\n🎉 All tests passed! Ready for Phase 3 development.\n")
        return True
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please fix before Phase 3.\n")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
