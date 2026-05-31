import math
"""
    Class za shranjevanje in vektorizacijo roke
"""
 
class Serializer:
    # Shrajene vse povezave med landmarki
    vse_povezave = [
        (0,1),(1,2),(2,3),(3,4),
        (0,5),(5,6),(6,7),(7,8),
        (5,9),(9,10),(10,11),(11,12),
        (9,13),(13,14),(14,15),(15,16),
        (13,17),(17,18),(18,19),(19,20),
        (0,17)
    ]
    # pretvorba povezav v list in normalizacija z skaliranjem...
    
    def landmark_norm(self, landmarks):
        llist = []
        
        for landmark in landmarks:
            llist.append([landmark.x, landmark.y, landmark.z])
            
        zapestje = llist[0]
        norm = []
        for mark in llist:
            norm.append([mark[0]- zapestje[0], mark[1]- zapestje[1], mark[2]- zapestje[2] ])
        scalar = norm[9]
        
        scale = math.sqrt(scalar[0] **2 + scalar[1] ** 2 + scalar[2] ** 2)
        if scale == 0:
            scale = 1
            
        out = []
        for poi in norm:
            out.append([poi[0]/ scale, poi[1]/ scale, poi[2]/ scale, ])
        
        # list vseh landmarkov in normaliziranje landmarke
        return llist, out
    
    # Pretvorba povezav v vektorje in sledeča normalizacija vektorjev...
    def vektor_handler(self, norm_landmarks):
        vektorji = []
        
        for S_i, e_i in self.vse_povezave:
            poi1 = norm_landmarks[S_i]
            poi2 = norm_landmarks[e_i]
            v = [ poi2[0] - poi1[0], poi2[1] - poi1[1], poi2[2] - poi1[2]]

            vektorji.append(v)

        # čas za normalizacijo
        
        normiči = []
        for vek in vektorji:
            d = math.sqrt(vek[0] **2 + vek[1] ** 2 + vek[2] ** 2) 
        
            # edgecase prekrivanja
            if d == 0:
                d = 1
                
            normiči.append([vek[0] / d, vek[1] / d, vek[2] / d])
            
        return vektorji, normiči
    
    def compres(self, data):
        #Samo za grupiranje koordinat ~ xyz,xyz -> xyzxyz
        flat = []
        for i in data:
            flat.extend(i)
        
        return flat
    
    def vektor_processor(self, landmarks):
        raw_marks, norm_marks = self.landmark_norm(landmarks)
        raw_vec, norm_vec = self.vektor_handler(norm_marks)
        f_vec = self.compres(norm_marks) + self.compres(norm_vec)
        return {
                    "raw_landmarks": raw_marks,
                    "normalized_landmarks": norm_marks,
                    "normalized_vectors": norm_vec,
                    "feature_vector": f_vec 
                }
        