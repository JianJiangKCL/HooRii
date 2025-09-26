#!/usr/bin/env python3
"""
Conversation Summary Service
Handles conversation summarization and storage
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

try:
    from langfuse import observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from ..models.database import Conversation
from ..utils.config import Config
from .database_service import DatabaseService


class ConversationSummaryService:
    """Service for managing conversation summaries"""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.database = DatabaseService(config)

    @observe(name="store_conversation_summary")
    async def store_conversation_summary(self, summary_data: Dict[str, Any]) -> bool:
        """Store conversation summary to database"""
        session = self.database.get_session()
        try:
            session_id = summary_data.get("session_id")

            # Get or create conversation record
            conversation = session.query(Conversation).filter_by(session_id=session_id).first()

            if not conversation:
                # Create new conversation record
                conversation = Conversation(
                    session_id=session_id,
                    user_id=summary_data.get("user_id", "default"),
                    start_time=datetime.fromisoformat(summary_data.get("start_time", datetime.utcnow().isoformat())),
                    end_time=datetime.fromisoformat(summary_data.get("end_time", datetime.utcnow().isoformat())),
                    message_count=summary_data.get("total_messages", 0),
                    summary=json.dumps(summary_data, ensure_ascii=False)
                )
                session.add(conversation)
            else:
                # Update existing conversation
                conversation.end_time = datetime.fromisoformat(summary_data.get("end_time", datetime.utcnow().isoformat()))
                conversation.message_count = summary_data.get("total_messages", 0)
                conversation.summary = json.dumps(summary_data, ensure_ascii=False)

            session.commit()
            self.logger.info(f"Stored conversation summary for session: {session_id}")
            return True

        except Exception as e:
            session.rollback()
            self.logger.error(f"Error storing conversation summary: {e}")
            return False
        finally:
            session.close()

    @observe(name="get_conversation_history")
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a user"""
        session = self.database.get_session()
        try:
            conversations = session.query(Conversation).filter_by(
                user_id=user_id
            ).order_by(desc(Conversation.start_time)).limit(limit).all()

            history = []
            for conv in conversations:
                try:
                    summary_data = json.loads(conv.summary) if conv.summary else {}
                    history.append({
                        "session_id": conv.session_id,
                        "start_time": conv.start_time.isoformat(),
                        "end_time": conv.end_time.isoformat() if conv.end_time else None,
                        "message_count": conv.message_count,
                        "summary": summary_data
                    })
                except json.JSONDecodeError:
                    continue

            return history

        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return []
        finally:
            session.close()

    @observe(name="generate_session_summary")
    async def generate_session_summary(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        device_actions: List[Dict[str, Any]] = None,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """Generate a comprehensive session summary"""

        try:
            # Extract key information from messages
            total_messages = len(messages)
            start_time = messages[0].get("timestamp", datetime.utcnow().isoformat()) if messages else datetime.utcnow().isoformat()
            end_time = messages[-1].get("timestamp", datetime.utcnow().isoformat()) if messages else datetime.utcnow().isoformat()

            # Analyze conversation topics
            topics = self._extract_topics(messages)

            # Analyze user behavior
            user_queries = [msg for msg in messages if msg.get("role") == "user"]
            assistant_responses = [msg for msg in messages if msg.get("role") == "assistant"]

            # Device interaction summary
            device_summary = self._summarize_device_actions(device_actions or [])

            # Familiarity progression
            familiarity_changes = self._analyze_familiarity_changes(messages)

            # Create comprehensive summary
            summary_data = {
                "session_id": session_id,
                "user_id": user_id,
                "start_time": start_time,
                "end_time": end_time,
                "total_messages": total_messages,
                "user_message_count": len(user_queries),
                "assistant_message_count": len(assistant_responses),
                "topics": topics,
                "device_actions": device_summary,
                "familiarity_changes": familiarity_changes,
                "session_duration_minutes": self._calculate_duration(start_time, end_time),
                "summary_generated_at": datetime.utcnow().isoformat()
            }

            # Store the summary
            success = await self.store_conversation_summary(summary_data)
            if success:
                self.logger.info(f"Generated and stored summary for session {session_id}")

            return summary_data

        except Exception as e:
            self.logger.error(f"Error generating session summary: {e}")
            return {
                "session_id": session_id,
                "user_id": user_id,
                "error": str(e),
                "summary_generated_at": datetime.utcnow().isoformat()
            }

    def _extract_topics(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract key topics from conversation messages"""
        topics = set()

        # Simple keyword-based topic extraction
        topic_keywords = {
            "device_control": ["灯", "电视", "空调", "音响", "窗帘", "light", "tv", "air", "speaker", "curtain"],
            "greeting": ["你好", "hello", "hi", "早上", "晚上"],
            "identity": ["主人", "名字", "身份", "谁"],
            "help": ["帮助", "help", "怎么", "如何"],
            "farewell": ["再见", "bye", "goodbye", "结束"]
        }

        for message in messages:
            content = message.get("content", "").lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in content for keyword in keywords):
                    topics.add(topic)

        return list(topics)

    def _summarize_device_actions(self, device_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize device interactions"""
        if not device_actions:
            return {"total_actions": 0, "devices_used": [], "success_rate": 0}

        devices_used = set()
        successful_actions = 0

        for action in device_actions:
            if action.get("device"):
                devices_used.add(action["device"])
            if action.get("success", False):
                successful_actions += 1

        return {
            "total_actions": len(device_actions),
            "devices_used": list(devices_used),
            "success_rate": successful_actions / len(device_actions) if device_actions else 0,
            "unique_devices": len(devices_used)
        }

    def _analyze_familiarity_changes(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze how familiarity might have changed during the session"""
        # This is a simplified analysis - in reality, you'd track actual familiarity score changes
        changes = []

        # Look for indicators of increasing familiarity
        user_messages = [msg for msg in messages if msg.get("role") == "user"]

        familiarity_indicators = {
            "polite_interaction": ["请", "谢谢", "麻烦"],
            "casual_interaction": ["嗨", "哈哈", "好的"],
            "trust_building": ["相信", "依靠", "帮忙"],
            "device_usage": ["开", "关", "调节", "控制"]
        }

        for i, message in enumerate(user_messages):
            content = message.get("content", "")
            for indicator_type, keywords in familiarity_indicators.items():
                if any(keyword in content for keyword in keywords):
                    changes.append({
                        "message_index": i,
                        "indicator": indicator_type,
                        "potential_change": "+1" if indicator_type in ["polite_interaction", "trust_building", "device_usage"] else "0"
                    })

        return changes

    def _calculate_duration(self, start_time: str, end_time: str) -> float:
        """Calculate session duration in minutes"""
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            duration = (end - start).total_seconds() / 60
            return round(duration, 2)
        except:
            return 0.0

    @observe(name="cleanup_old_summaries")
    async def cleanup_old_summaries(self, days_old: int = 30) -> int:
        """Clean up old conversation summaries"""
        session = self.database.get_session()
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            # Delete old conversations
            deleted_count = session.query(Conversation).filter(
                Conversation.start_time < cutoff_date
            ).delete()

            session.commit()
            self.logger.info(f"Cleaned up {deleted_count} old conversation summaries")
            return deleted_count

        except Exception as e:
            session.rollback()
            self.logger.error(f"Error cleaning up conversations: {e}")
            return 0
        finally:
            session.close()

    def get_user_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """Get conversation statistics for a user"""
        session = self.database.get_session()
        try:
            conversations = session.query(Conversation).filter_by(user_id=user_id).all()

            if not conversations:
                return {"total_conversations": 0, "total_messages": 0, "avg_session_length": 0}

            total_conversations = len(conversations)
            total_messages = sum(conv.message_count for conv in conversations)
            avg_messages = total_messages / total_conversations if total_conversations > 0 else 0

            return {
                "user_id": user_id,
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "avg_messages_per_session": round(avg_messages, 2),
                "most_recent_session": conversations[-1].start_time.isoformat() if conversations else None
            }

        except Exception as e:
            self.logger.error(f"Error getting user conversation stats: {e}")
            return {"error": str(e)}
        finally:
            session.close()