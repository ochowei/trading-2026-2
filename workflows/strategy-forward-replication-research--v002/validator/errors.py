"""Workflow 驗證使用的錯誤型別。"""


class WorkflowError(Exception):
    """所有 workflow 錯誤的基底。"""


class ValidationError(WorkflowError):
    """輸入不符合 workflow 規則。"""


class IntegrityError(WorkflowError):
    """不可變資料、digest chain 或 authority 發生不一致。"""


class TransitionError(ValidationError):
    """Study Event 轉移不合法。"""


class EvidenceUnavailable(WorkflowError):
    """必要 evidence 無法取得或重算。"""
