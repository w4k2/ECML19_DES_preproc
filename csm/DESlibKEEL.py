"""
Dumb Delay Pool.
"""

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_X_y, check_array
from sklearn.ensemble import BaggingClassifier
from sklearn import neighbors
from sklearn.metrics import f1_score, balanced_accuracy_score
from deslib.des import KNORAE, KNORAU, DESKNN, DESClustering
from imblearn.over_sampling import RandomOverSampler, SMOTE, SVMSMOTE, BorderlineSMOTE, ADASYN
from imblearn.metrics  import geometric_mean_score
from smote_variants import Safe_Level_SMOTE
import smote_variants as sv

ba = balanced_accuracy_score
f1 = f1_score
gmean = geometric_mean_score


class DESlibKEEL(BaseEstimator, ClassifierMixin):
    """
        note
    """

    def __init__(
        self, ensemble_size=3, desMethod="KNORAE", oversampled=True
    ):
        """Initialization."""
        self.ensemble_size = ensemble_size
        self.desMethod = desMethod
        self.oversampled = oversampled

    def set_base_clf(self, base_clf=BaggingClassifier(
                                neighbors.KNeighborsClassifier(),
                                n_estimators=100,
                                max_samples=0.5, max_features=1.0,
                                bootstrap_features=False, random_state=42,
                                bootstrap=True)):
        """Establish base classifier."""
        self._base_clf = base_clf

    # Fitting
    def fit(self, X, y):
        """Fitting."""
        if not hasattr(self, "_base_clf"):
            self.set_base_clf()

        X, y = check_X_y(X, y)
        self.X_ = X
        self.y_ = y

        self.X_dsel = X
        self.y_dsel = y

        if self.oversampled:
            smote = SMOTE(random_state=42)
            rand = RandomOverSampler(random_state=42)
            # sls = sv.SMOTE()
            try:
                X, y = smote.fit_resample(X, y)
                # X, y = sls.sample(X, y)
            except ValueError:
                print("Leci random")
                X, y = rand.fit_resample(X, y)

        self._base_clf.fit(X, y)
        # Return the classifier
        return self

    def predict(self, X):
        """Hard decision."""
        # print("PREDICT")
        # Check is fit had been called
        # check_is_fitted(self, "classes_")

        # Input validation
        X = check_array(X)
        if X.shape[1] != self.X_.shape[1]:
            raise ValueError("number of features does not match")

        if self.oversampled:
            smote = SMOTE(random_state=42)
            rand = RandomOverSampler(random_state=42)
            sls = sv.SMOTE()
            try:
                self.X_dsel, self.y_dsel = smote.fit_resample(self.X_dsel, self.y_dsel)
                # self.X_dsel, self.y_dsel = sls.sample(self.X_dsel, self.y_dsel)
            except ValueError:
                self.X_dsel, self.y_dsel = rand.fit_resample(self.X_dsel, self.y_dsel)

        if self.desMethod == "KNORAE":
            des = KNORAE(self._base_clf.estimators_, random_state=42)
            des.fit(self.X_, self.y_)
            prediction = des.predict(X)
        elif self.desMethod == "KNORAU":
            des = KNORAU(self._base_clf.estimators_, random_state=42)
            des.fit(self.X_dsel, self.y_dsel)
            prediction = des.predict(X)
        elif self.desMethod == "KNN":
            des = DESKNN(self._base_clf.estimators_, random_state=42)
            des.fit(self.X_dsel, self.y_dsel)
            prediction = des.predict(X)
        elif self.desMethod == "Clustering":
            des = DESClustering(self._base_clf.estimators_, random_state=42)
            des.fit(self.X_dsel, self.y_dsel)
            prediction = des.predict(X)
        else:
            prediction = self._base_clf.predict(X)


        return prediction

    def score(self, X, y):
        return ba(y, self.predict(X)), f1(y, self.predict(X)), gmean(y, self.predict(X))
