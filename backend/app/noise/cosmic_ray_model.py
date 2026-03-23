import numpy as np

class CosmicRayNoiseModel:
    """
    نموذج يحاكي تأثير الأشعة الكونية (الميونات) على مصفوفة الكيوبتات.
    يسبب أخطاء مترابطة (Correlated Errors) مكانياً وزمانياً.
    """
    def __init__(self, flux_rate=0.01, ionization_radius=2.5):
        self.flux_rate = flux_rate  # معدل تدفق الأشعة الكونية
        self.ionization_radius = ionization_radius  # قطر منطقة التأين (بالكيوبتات)

    def apply_cosmic_event(self, qubit_topology):
        """
        يحدد الكيوبتات المتأثرة بحدث كوني واحد بناءً على توبولوجيا الجهاز.
        """
        # اختيار مركز عشوائي لارتطام الجسيم الكوني على الشريحة
        impact_point = np.random.uniform(0, qubit_topology.dim)
        
        affected_qubits = []
        for qubit in qubit_topology.qubits:
            distance = np.linalg.norm(qubit.pos - impact_point)
            if distance <= self.ionization_radius:
                # توليد خطأ مترابط (Burst Error)
                affected_qubits.append(qubit.id)
        
        return affected_qubits

    def get_error_probability(self, is_cosmic_event):
        """
        يرفع احتمالية الخطأ بشكل حاد عند حدوث 'تسمم أشباه الجسيمات'.
        """
        return 0.95 if is_cosmic_event else 0.001
