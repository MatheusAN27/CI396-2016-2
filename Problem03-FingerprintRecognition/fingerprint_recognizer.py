from processed_image import ProcessedImage
from scipy.spatial import distance
import numpy as np


class FingerprintRecognizer:
    def __init__(self, trainingImages, trainingLabels):
        self.trainingSet = []
        for image, label in zip(trainingImages, trainingLabels):
            self.trainingSet.append(
                ProcessedImage(image, label)
            )

    def predict(self, image):
        test_image = ProcessedImage(image, 'none')
        min_s_index = 0
        min_s = 0
        for index, train_image in enumerate(self.trainingSet):
            if train_image.classification != test_image.classification:
                continue
            s = self._calculate_s(train_image, test_image)
            if min_s < s:
                min_s_index = index
                min_s = s
        label = self.trainingSet[min_s_index].label
        return label

    def _calculate_s(self, train, test, radius=16):
        potencial_minutiaes = []
        train_minutiaes = train.transformed_minutiaes
        test_minutiaes = test.transformed_minutiaes
        for train_minutiae in train_minutiaes:
            for test_minutiae in test_minutiaes:
                dist = distance.euclidean(train_minutiae, test_minutiae)
                if dist <= radius:
                    potencial_minutiaes.append(dist)
        if len(potencial_minutiaes) < 1:
            return -1
        potencial_minutiaes = np.array(potencial_minutiaes)
        summatory = np.sum(1 - potencial_minutiaes / radius)
        s = 100/len(potencial_minutiaes) * summatory
        return s