"""
Prompt 模板库 — 预定义的场景模板，一键应用到系统提示词或输入框。
"""

from dataclasses import dataclass


@dataclass
class PromptTemplate:
    id: str
    emoji: str
    title: str
    description: str
    system_prompt: str
    suggested_message: str = ''


TEMPLATES: list[PromptTemplate] = [
    PromptTemplate(
        id='code-review', emoji='🔍', title='代码审查',
        description='让 AI 以资深架构师视角审查你的代码',
        system_prompt='你是一位资深软件架构师，擅长代码审查。请从以下维度审查代码：1）正确性；2）性能；3）可维护性；4）安全性。给出改进建议。',
        suggested_message='请审查以下代码：'),
    PromptTemplate(
        id='translator', emoji='🌐', title='翻译助手',
        description='中英文互译，保留语境和语气',
        system_prompt='你是一位专业翻译。原则：1）准确传达原意；2）符合目标语言习惯；3）保留原文语气。',
        suggested_message='请将以下内容翻译成英文：'),
    PromptTemplate(
        id='writer', emoji='✍️', title='写作润色',
        description='改进文章表达，优化文笔和逻辑',
        system_prompt='你是一位专业写作编辑。请对用户输入进行润色：优化句子结构、改进用词、调整逻辑顺序。',
        suggested_message='请帮我润色以下这段文字：'),
    PromptTemplate(
        id='interview', emoji='🎯', title='面试模拟',
        description='模拟技术面试，对岗位出题和点评',
        system_prompt='你是一位资深技术面试官。请模拟真实面试：逐步出题、给出评分和改进建议。',
        suggested_message='我想模拟一次 Python 后端开发的面试。'),
    PromptTemplate(
        id='summary', emoji='📝', title='内容总结',
        description='快速总结长文、会议记录或文章',
        system_prompt='你是一个内容总结专家。提取核心观点、按逻辑组织、保留重要数据。',
        suggested_message='请帮我总结以下内容：'),
    PromptTemplate(
        id='brainstorm', emoji='💡', title='头脑风暴',
        description='发散思维，生成创意点子',
        system_prompt='你是创意策划专家。围绕主题提出至少5个创意方向，每个给出2-3个具体点子。',
        suggested_message='我需要关于「」的创意，帮我 brainstorm 一下。'),
    PromptTemplate(
        id='learning', emoji='📖', title='学习助手',
        description='解释概念、提供示例、出题巩固',
        system_prompt='你是一位耐心的 tutor。用通俗的语言解释核心概念，给出示例，提供练习题。',
        suggested_message='请帮我解释「」这个概念，我是一名初学者。'),
    PromptTemplate(
        id='debug', emoji='🐛', title='Debug 助手',
        description='分析错误信息，定位并修复 Bug',
        system_prompt='你是一位调试专家。分析错误信息定位问题根源，解释原因，给出修复方案。',
        suggested_message='我遇到了这个错误：'),
]


def get_template(template_id: str) -> PromptTemplate | None:
    for t in TEMPLATES:
        if t.id == template_id:
            return t
    return None


def list_templates() -> list[dict]:
    return [
        {'id': t.id, 'emoji': t.emoji, 'title': t.title, 'description': t.description}
        for t in TEMPLATES
    ]
