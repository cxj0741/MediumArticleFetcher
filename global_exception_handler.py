import sys
import traceback
from logger_config import logger

class GlobalExceptionHandler:
    @staticmethod
    def setup():
        """设置全局异常处理器"""
        sys.excepthook = GlobalExceptionHandler.handle_exception

    @staticmethod
    def handle_exception(exc_type, exc_value, exc_traceback):
        """处理未捕获的异常"""
        if issubclass(exc_type, KeyboardInterrupt):
            # 忽略 KeyboardInterrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        else:
            # print("Unhandled exception:")
            logger.info("Unhandled exception:")
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            logger.error("Exception details:", exc_info=(exc_type, exc_value, exc_traceback))
            # 你可以在这里进行日志记录或其他处理


