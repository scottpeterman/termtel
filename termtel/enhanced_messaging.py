"""
Enhanced Plugin Messaging System
Handles message passing between plugins and main application
"""
from typing import Dict, Any, Callable, Optional
from enum import Enum, auto
import logging
import json
from dataclasses import dataclass, asdict
from pathlib import Path
import multiprocessing as mp

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Standard message types for plugin communication"""
    INITIALIZE = auto()  # Initialize plugin with basic settings
    CLEANUP = auto()  # Clean up plugin resources
    THEME_CHANGED = auto()  # Theme has been changed in main app
    GET_CREDENTIALS = auto()  # Request specific credential
    LIST_CREDENTIALS = auto()  # Request list of available credentials
    ERROR = auto()  # Error message
    EXIT = auto()  # Exit signal for plugin


@dataclass
class MessageEnvelope:
    """Message envelope for custom plugin data"""
    action: str
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PluginMessage:
    """Standard message format for plugin communication"""
    type: MessageType
    data: Dict[str, Any]
    plugin_id: Optional[str] = None
    sequence_id: Optional[int] = None
    envelope: Optional[MessageEnvelope] = None

    def to_dict(self):
        """Convert message to dictionary for transmission"""
        msg_dict = asdict(self)
        msg_dict['type'] = self.type.name  # Convert enum to string
        return msg_dict

    @classmethod
    def from_dict(cls, data: Dict):
        """Create message from dictionary"""
        data['type'] = MessageType[data['type']]  # Convert string to enum
        return cls(**data)


class PluginMessageBroker:
    """Manages message passing between plugin and main app"""

    def __init__(self, pipe_conn, plugin_id: str):
        self.pipe_conn = pipe_conn
        self.plugin_id = plugin_id
        self.sequence = 0

    def send_message(self, msg_type: MessageType, data: Dict[str, Any],
                     envelope: Optional[MessageEnvelope] = None) -> Dict[str, Any]:
        """Send a message and wait for response"""
        message = PluginMessage(
            type=msg_type,
            data=data,
            plugin_id=self.plugin_id,
            sequence_id=self.sequence,
            envelope=envelope
        )
        self.sequence += 1

        self.pipe_conn.send(message.to_dict())
        return self.pipe_conn.recv()

    def send_generic(self, action: str, payload: Dict[str, Any],
                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a generic message with custom action and payload"""
        envelope = MessageEnvelope(action=action, payload=payload, metadata=metadata)
        return self.send_message(MessageType.GENERIC, {}, envelope=envelope)


class MessageDispatcher:
    """Handles message routing and callbacks"""

    def __init__(self):
        self.handlers: Dict[MessageType, Callable] = {}
        self.generic_handlers: Dict[str, Callable] = {}

    def register_handler(self, msg_type: MessageType, handler: Callable):
        """Register a handler for a message type"""
        self.handlers[msg_type] = handler

    def register_generic_handler(self, action: str, handler: Callable):
        """Register a handler for a generic message action"""
        self.generic_handlers[action] = handler

    def dispatch_message(self, message: PluginMessage) -> Dict[str, Any]:
        """Dispatch a message to appropriate handler"""
        try:
            if message.type == MessageType.GENERIC and message.envelope:
                if message.envelope.action in self.generic_handlers:
                    return self.generic_handlers[message.envelope.action](
                        message.envelope.payload,
                        message.envelope.metadata,
                        message.plugin_id
                    )
                else:
                    return {"status": "error", "message": f"No handler for action: {message.envelope.action}"}
            elif message.type in self.handlers:
                return self.handlers[message.type](message.data, message.plugin_id)
            else:
                return {"status": "error", "message": f"No handler for message type: {message.type}"}
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return {"status": "error", "message": str(e)}


class PluginProcess(mp.Process):
    """Runs a plugin in its own process"""

    def __init__(self, plugin_path: str, pipe_conn, theme_name: str):
        super().__init__()
        self.plugin_path = plugin_path
        self.pipe_conn = pipe_conn
        self.theme_name = theme_name
        self.daemon = True

    def run(self):
        """Main plugin process loop"""
        try:
            # Import and initialize the plugin
            module = self._load_plugin_module()
            plugin = module.Plugin()
            broker = PluginMessageBroker(self.pipe_conn, Path(self.plugin_path).stem)

            # Main message loop
            while True:
                try:
                    msg_dict = self.pipe_conn.recv()
                    message = PluginMessage.from_dict(msg_dict)

                    if message.type == MessageType.EXIT:
                        break

                    response = self._handle_message(message, plugin, broker)
                    self.pipe_conn.send(response)

                except EOFError:
                    break
                except Exception as e:
                    logger.error(f"Error in plugin message loop: {e}")
                    self.pipe_conn.send({"status": "error", "message": str(e)})

        except Exception as e:
            logger.error(f"Plugin process error: {e}")
            self.pipe_conn.send({"status": "error", "message": str(e)})

    def _load_plugin_module(self):
        """Load the plugin module"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("plugin_module", self.plugin_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load plugin: {self.plugin_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _handle_message(self, message: PluginMessage, plugin, broker) -> Dict[str, Any]:
        """Handle a specific message"""
        try:
            if message.type == MessageType.INITIALIZE:
                plugin.initialize(message.data.get("theme_colors", {}), broker)
                return {"status": "ok"}

            elif message.type == MessageType.CLEANUP:
                plugin.cleanup()
                return {"status": "ok"}

            elif message.type == MessageType.THEME_CHANGED:
                plugin.theme_changed(
                    message.data.get("theme_name", ""),
                    message.data.get("theme_colors", {})
                )
                return {"status": "ok"}

            else:
                return {"status": "error", "message": f"Unhandled message type: {message.type}"}

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {"status": "error", "message": str(e)}


class PluginManager:
    """Manages plugin lifecycle and communication"""

    def __init__(self, theme_manager, dispatcher: MessageDispatcher):
        self.theme_manager = theme_manager
        self.dispatcher = dispatcher
        self.processes: Dict[str, tuple[PluginProcess, Any]] = {}
        self.current_theme = "cyberpunk"

    def load_plugin(self, plugin_path: str, mp) -> bool:
        """Load and initialize a plugin"""
        try:
            parent_conn, child_conn = mp.Pipe()
            process = PluginProcess(plugin_path, child_conn, self.current_theme)
            process.start()

            plugin_id = Path(plugin_path).stem
            self.processes[plugin_id] = (process, parent_conn)

            # Initialize plugin with current theme
            theme_colors = self._get_theme_colors()
            response = self._send_message(
                plugin_id,
                MessageType.INITIALIZE,
                {"theme_colors": theme_colors}
            )

            if response["status"] != "ok":
                raise Exception(response["message"])

            return True

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_path}: {e}")
            return False

    def _get_theme_colors(self) -> Dict[str, Any]:
        """Get current theme colors"""
        colors = self.theme_manager.get_colors(self.current_theme)
        return {k: str(v) for k, v in colors.items()}

    def _send_message(self, plugin_id: str, msg_type: MessageType,
                      data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to a specific plugin"""
        if plugin_id not in self.processes:
            return {"status": "error", "message": f"Plugin not found: {plugin_id}"}

        _, conn = self.processes[plugin_id]
        message = PluginMessage(type=msg_type, data=data, plugin_id=plugin_id)
        conn.send(message.to_dict())
        return conn.recv()

    def notify_theme_changed(self, theme_name: str):
        """Notify all plugins of theme change"""
        self.current_theme = theme_name
        theme_colors = self._get_theme_colors()

        for plugin_id in self.processes:
            self._send_message(
                plugin_id,
                MessageType.THEME_CHANGED,
                {
                    "theme_name": theme_name,
                    "theme_colors": theme_colors
                }
            )

    def cleanup(self):
        """Clean up all plugins"""
        for plugin_id in list(self.processes.keys()):
            self.unload_plugin(plugin_id)

    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a specific plugin"""
        try:
            if plugin_id in self.processes:
                process, conn = self.processes[plugin_id]
                self._send_message(plugin_id, MessageType.CLEANUP, {})
                conn.send(PluginMessage(
                    type=MessageType.EXIT,
                    data={},
                    plugin_id=plugin_id
                ).to_dict())

                process.join(timeout=5)
                if process.is_alive():
                    process.terminate()

                del self.processes[plugin_id]
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False