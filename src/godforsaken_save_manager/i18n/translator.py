"""
国际化(i18n)翻译器模块
提供多语言支持功能，包括语言自动检测、翻译加载和文本获取
"""

import json
import os
import locale
from pathlib import Path
from typing import Dict, Optional

from ..common.paths import get_base_path


class Language:
    """支持的语言枚举"""
    CHINESE_SIMPLIFIED = "zh_CN"
    ENGLISH = "en_US"

    @staticmethod
    def get_display_name(language_code: str) -> str:
        """获取语言的显示名称"""
        display_names = {
            Language.CHINESE_SIMPLIFIED: "简体中文",
            Language.ENGLISH: "English"
        }
        return display_names.get(language_code, language_code)

    @staticmethod
    def get_all_languages() -> Dict[str, str]:
        """获取所有支持的语言"""
        return {
            Language.CHINESE_SIMPLIFIED: Language.get_display_name(Language.CHINESE_SIMPLIFIED),
            Language.ENGLISH: Language.get_display_name(Language.ENGLISH)
        }


class Translator:
    """翻译器类，负责加载和管理多语言文本"""

    def __init__(self):
        self._current_language: Optional[str] = None
        self._translations: Dict[str, Dict[str, str]] = {}
        self._base_path = get_base_path()

    def get_available_languages(self) -> Dict[str, str]:
        """获取可用的语言列表"""
        return Language.get_all_languages()

    def detect_system_language(self) -> str:
        """自动检测系统语言"""
        try:
            # 获取系统默认语言
            system_locale = locale.getdefaultlocale()[0]

            if system_locale:
                # 处理中文语言代码
                if system_locale.startswith('zh'):
                    return Language.CHINESE_SIMPLIFIED
                # 处理英文语言代码
                elif system_locale.startswith('en'):
                    return Language.ENGLISH

            # 默认返回英文
            return Language.ENGLISH

        except Exception:
            # 检测失败时默认返回英文
            return Language.ENGLISH

    def load_translations(self, language_code: str) -> bool:
        """加载指定语言的翻译文件"""
        translation_file = self._base_path / "i18n" / f"{language_code}.json"

        if not translation_file.exists():
            # 如果指定语言文件不存在，回退到英文
            if language_code != Language.ENGLISH:
                return self.load_translations(Language.ENGLISH)
            return False

        try:
            with open(translation_file, 'r', encoding='utf-8') as f:
                self._translations[language_code] = json.load(f)
            self._current_language = language_code
            return True
        except Exception as e:
            print(f"加载翻译文件失败: {e}")
            # 加载失败时回退到英文
            if language_code != Language.ENGLISH:
                return self.load_translations(Language.ENGLISH)
            return False

    def set_language(self, language_code: str) -> bool:
        """设置当前语言"""
        if language_code in self.get_available_languages():
            return self.load_translations(language_code)
        return False

    def get_current_language(self) -> Optional[str]:
        """获取当前语言代码"""
        return self._current_language

    def t(self, key: str, **kwargs) -> str:
        """
        获取翻译文本
        :param key: 翻译键，支持点分隔的层级结构，如 'ui.main_window.title'
        :param kwargs: 格式化参数，用于字符串格式化
        :return: 翻译后的文本，如果找不到则返回键名
        """
        if not self._current_language or self._current_language not in self._translations:
            return key

        # 解析层级键
        keys = key.split('.')
        current_dict = self._translations[self._current_language]

        try:
            for k in keys:
                current_dict = current_dict[k]

            text = current_dict

            # 如果提供了格式化参数，则进行格式化
            if kwargs:
                try:
                    text = text.format(**kwargs)
                except (KeyError, ValueError):
                    # 格式化失败时返回原始文本
                    pass

            return text

        except (KeyError, TypeError):
            # 如果找不到翻译，返回键名
            return key

    def get_language_name(self, language_code: str) -> str:
        """获取语言的本地化名称"""
        if language_code == Language.CHINESE_SIMPLIFIED:
            return self.t('language.chinese_simplified')
        elif language_code == Language.ENGLISH:
            return self.t('language.english')
        return Language.get_display_name(language_code)


# 全局翻译器实例
_translator = Translator()


def init_translator(language_code: Optional[str] = None) -> bool:
    """
    初始化翻译器
    :param language_code: 指定语言代码，如果为None则自动检测系统语言
    :return: 初始化是否成功
    """
    if language_code is None:
        language_code = _translator.detect_system_language()

    return _translator.set_language(language_code)


def get_translator() -> Translator:
    """获取全局翻译器实例"""
    return _translator


def t(key: str, **kwargs) -> str:
    """全局翻译函数"""
    return _translator.t(key, **kwargs)


def set_language(language_code: str) -> bool:
    """设置语言的全局函数"""
    return _translator.set_language(language_code)


def get_current_language() -> Optional[str]:
    """获取当前语言的全局函数"""
    return _translator.get_current_language()


def get_available_languages() -> Dict[str, str]:
    """获取可用语言列表的全局函数"""
    return _translator.get_available_languages()