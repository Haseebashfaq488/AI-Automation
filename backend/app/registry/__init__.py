from .tool_registry import ToolRegistry

# WhatsApp module
from app.modules.whatsapp.tools.send_message import SendMessageTool
from app.modules.whatsapp.tools.send_file import SendFileTool
from app.modules.whatsapp.tools.list_chats import ListChatsTool
from app.modules.whatsapp.tools.get_messages import GetMessagesTool
from app.modules.whatsapp.tools.search_messages import SearchMessagesTool
from app.modules.whatsapp.tools.get_chat_info import GetChatInfoTool
from app.modules.whatsapp.tools.list_contacts import ListContactsTool
from app.modules.whatsapp.tools.manage_chat import ManageChatTool
from app.modules.whatsapp.tools.manage_group import ManageGroupTool
from app.modules.whatsapp.tools.download_media import DownloadMediaTool
from app.modules.whatsapp.tools.get_status import GetStatusTool
from app.modules.whatsapp.tools.get_unread_messages import GetUnreadMessagesTool
from app.modules.whatsapp.tools.get_recent_whatsapp_activity import GetRecentWhatsAppActivityTool
from app.modules.whatsapp.tools.get_whatsapp_chat_messages import GetWhatsAppChatMessagesTool
from app.modules.whatsapp.skills.send_report import SendReportSkill
from app.modules.whatsapp.skills.unread_digest import UnreadDigestSkill

# Global registry instance
registry = ToolRegistry()
# Gmail tools & skills
from app.modules.gmail.tools.send_email_tool import SendEmailTool
from app.modules.gmail.skills.list_recent_emails import ListRecentEmailsSkill

registry.register(SendEmailTool())
registry.register(ListRecentEmailsSkill())

# Google Drive tools & skills
from app.modules.drive.tools.list_drive_files import ListDriveFilesTool
from app.modules.drive.tools.read_drive_file import ReadDriveFileTool
from app.modules.drive.tools.upload_drive_file import UploadDriveFileTool
from app.modules.drive.skills.search_drive import SearchDriveSkill

registry.register(ListDriveFilesTool())
registry.register(ReadDriveFileTool())
registry.register(UploadDriveFileTool())
registry.register(SearchDriveSkill())
# WhatsApp tools & skills
registry.register(SendMessageTool())
registry.register(SendFileTool())
registry.register(ListChatsTool())
registry.register(GetMessagesTool())
registry.register(GetWhatsAppChatMessagesTool())
registry.register(GetUnreadMessagesTool())
registry.register(GetRecentWhatsAppActivityTool())
registry.register(SearchMessagesTool())
registry.register(GetChatInfoTool())
registry.register(ListContactsTool())
registry.register(ManageChatTool())
registry.register(ManageGroupTool())
registry.register(DownloadMediaTool())
registry.register(GetStatusTool())
registry.register(SendReportSkill())
registry.register(UnreadDigestSkill())

# Autonomous Worker Fork Tool
from app.workers.tools.fork_tool import ForkTool
registry.register(ForkTool())

# System Power Management Tools
from app.modules.system.tools.shutdown_tool import ShutdownTool
from app.modules.system.tools.cancel_shutdown_tool import CancelShutdownTool
registry.register(ShutdownTool())
registry.register(CancelShutdownTool())

