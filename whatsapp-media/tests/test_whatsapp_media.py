#!/usr/bin/env python3
"""
Tests for whatsapp-media skill.
Tests structure, script syntax, and basic functionality.
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
SCRIPT_PATH = SKILL_DIR / "scripts" / "process-media.sh"


class TestSkillStructure(unittest.TestCase):
    """Test skill file structure."""
    
    def test_skill_md_exists(self):
        """SKILL.md should exist."""
        skill_md = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_md.exists(), "SKILL.md not found")
    
    def test_skill_md_has_frontmatter(self):
        """SKILL.md should have YAML frontmatter with name and description."""
        skill_md = SKILL_DIR / "SKILL.md"
        content = skill_md.read_text()
        
        self.assertTrue(content.startswith("---"), "Missing frontmatter start")
        self.assertIn("name:", content, "Missing name field")
        self.assertIn("description:", content, "Missing description field")
    
    def test_scripts_directory_exists(self):
        """Scripts directory should exist."""
        scripts_dir = SKILL_DIR / "scripts"
        self.assertTrue(scripts_dir.exists(), "scripts/ not found")
    
    def test_process_media_script_exists(self):
        """process-media.sh should exist and be executable."""
        self.assertTrue(SCRIPT_PATH.exists(), "process-media.sh not found")
        self.assertTrue(os.access(SCRIPT_PATH, os.X_OK), "process-media.sh not executable")


class TestScriptSyntax(unittest.TestCase):
    """Test script syntax validity."""
    
    def test_bash_syntax_valid(self):
        """process-media.sh should have valid bash syntax."""
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT_PATH)],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Syntax error: {result.stderr}")


class TestScriptHelp(unittest.TestCase):
    """Test script help and usage."""
    
    def test_usage_shown_on_no_args(self):
        """Script should show usage when called without arguments."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH)],
            capture_output=True,
            text=True
        )
        # Script exits with error and shows usage
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)
    
    def test_usage_contains_commands(self):
        """Usage should list available commands."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH)],
            capture_output=True,
            text=True
        )
        output = result.stdout
        self.assertIn("image", output)
        self.assertIn("audio", output)
        self.assertIn("list-images", output)
        self.assertIn("list-audio", output)


class TestListCommands(unittest.TestCase):
    """Test list commands (don't require media files)."""
    
    def test_list_images_runs(self):
        """list-images command should run without error."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "list-images"],
            capture_output=True,
            text=True,
            env={**os.environ, "CLAWDBOT_MEDIA_DIR": "/tmp"}
        )
        # Should succeed even if no images found
        self.assertEqual(result.returncode, 0)
        self.assertIn("Recent images", result.stdout)
    
    def test_list_audio_runs(self):
        """list-audio command should run without error."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "list-audio"],
            capture_output=True,
            text=True,
            env={**os.environ, "CLAWDBOT_MEDIA_DIR": "/tmp"}
        )
        # Should succeed even if no audio found
        self.assertEqual(result.returncode, 0)
        self.assertIn("Recent audio", result.stdout)


class TestImageCommand(unittest.TestCase):
    """Test image analysis command."""
    
    def test_image_missing_file_arg(self):
        """image command should fail if no file provided."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "image"],
            capture_output=True,
            text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error: file required", result.stdout)
    
    def test_image_nonexistent_file(self):
        """image command should fail for nonexistent file."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "image", "/nonexistent/file.jpg"],
            capture_output=True,
            text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("File not found", result.stderr)
    
    def test_image_with_valid_file(self):
        """image command should output path for valid file."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"fake image data")
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ["bash", str(SCRIPT_PATH), "image", temp_path],
                capture_output=True,
                text=True
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("IMAGE_PATH=", result.stdout)
            self.assertIn(temp_path, result.stdout)
        finally:
            os.unlink(temp_path)


class TestAudioCommand(unittest.TestCase):
    """Test audio transcription command."""
    
    def test_audio_missing_file_arg(self):
        """audio command should fail if no file provided."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "audio"],
            capture_output=True,
            text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error: file required", result.stdout)
    
    def test_audio_nonexistent_file(self):
        """audio command should fail for nonexistent file."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "audio", "/nonexistent/file.ogg"],
            capture_output=True,
            text=True,
            env={**os.environ, "GROQ_API_KEY": "test"}
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("File not found", result.stderr)
    
    def test_audio_checks_for_api_key(self):
        """Script source code should check for GROQ_API_KEY."""
        # Verify the script has API key validation logic
        script_content = SCRIPT_PATH.read_text()
        self.assertIn("GROQ_API_KEY", script_content)
        self.assertIn("not set", script_content)


class TestRecentCommands(unittest.TestCase):
    """Test recent-* commands."""
    
    def test_recent_image_exits_nonzero_when_no_files(self):
        """recent-image should exit non-zero when no files found."""
        # Use an empty temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["bash", str(SCRIPT_PATH), "recent-image"],
                capture_output=True,
                text=True,
                env={**os.environ, "CLAWDBOT_MEDIA_DIR": tmpdir}
            )
            # Should fail with non-zero exit
            self.assertNotEqual(result.returncode, 0)
    
    def test_recent_audio_exits_nonzero_when_no_files(self):
        """recent-audio should exit non-zero when no files found."""
        # Use an empty temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["bash", str(SCRIPT_PATH), "recent-audio"],
                capture_output=True,
                text=True,
                env={**os.environ, "CLAWDBOT_MEDIA_DIR": tmpdir}
            )
            # Should fail with non-zero exit
            self.assertNotEqual(result.returncode, 0)
    
    def test_script_has_recent_file_logic(self):
        """Script should have find logic for recent files."""
        script_content = SCRIPT_PATH.read_text()
        self.assertIn("find_recent_image", script_content)
        self.assertIn("find_recent_audio", script_content)
        self.assertIn("-mmin", script_content)  # Looks for recent files


if __name__ == "__main__":
    unittest.main()
