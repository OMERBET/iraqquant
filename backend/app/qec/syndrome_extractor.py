import numpy as np

class CosmicSyndromeExtractor:
    """
    مستخرج المتلازمة (Syndrome Extractor) المتخصص في كشف أخطاء الأشعة الكونية.
    يقوم برصد 'انفجارات الأخطاء' (Error Bursts) وتحديد الكيوبتات المنطقية المتضررة.
    """
    def __init__(self, code_distance=3):
        self.code_distance = code_distance # المسافة البرمجية للكود (مثل Surface Code)

    def check_for_burst_errors(self, measurement_results, impacted_qubits):
        """
        يحلل نتائج القياس لاكتشاف ما إذا كان هناك خطأ جماعي (Cosmic Burst).
        """
        detected_syndromes = []
        for q_id in impacted_qubits:
            if measurement_results.get(q_id) == 1: # إذا تغيرت حالة الكيوبت بشكل غير متوقع
                detected_syndromes.append(f"Qubit_{q_id}_flipped")
        
        return {
            "event_type": "Cosmic_Ionization" if len(detected_syndromes) > 1 else "Random_Noise",
            "syndromes": detected_syndromes,
            "confidence_score": len(detected_syndromes) / (self.code_distance**2)
        }

    def trigger_correction(self, syndrome_report):
        """
        يرسل إشارة للمحرك (Core) لتطبيق بوابة التصحيح (Pauli X/Z) لإعادة الحالة الأصلية.
        """
        if syndrome_report["confidence_score"] > 0.5:
            return "Apply_Global_Recalibration" # إعادة معايرة شاملة بسبب قوة الإشعاع
        return "Apply_Local_X_Gate"
