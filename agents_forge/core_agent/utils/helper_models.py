from enum import Enum

class NextStep(str, Enum):
        UPDATE_BLUEPRINT = "update_blueprint"
        ASK_FOLLOWUP = "ask_followup"
        GENERATE_AGENT = "generate_agent"
        EVALUATE_BLUEPRINT = "evaluate_blueprint"
        