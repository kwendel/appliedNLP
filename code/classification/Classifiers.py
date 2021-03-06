import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import chi2, mutual_info_classif
from sklearn.model_selection import GridSearchCV, KFold, cross_validate
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

"""
Example of the classifier input:
classifiers = [
    {
        'name': 'RandomForest',
        'clf': RandomForestClassifier(),
        // Either define grid and call .optimize(), or define optimized_param
        'grid': {
            'n_estimators': [100, 1000],
            'max_depth': [2, 3]
        },
        optimized_param: {
            max_depth: 3,
            n_estimators: 100,
        }
    }
]

"""

metrics = ['accuracy', 'precision', 'f1', 'roc_auc', 'recall']
classnames = ['no-clickbait', 'clickbait']


class Classifiers:
    def __init__(self, feature_df: pd.DataFrame, labels, classifiers):
        self.df = feature_df
        # Extract the dataframe as a numpy array
        self.data = feature_df.to_numpy()
        self.labels = labels

        self.classifiers = classifiers

    def information_gain(self, data=None):
        # Use data from class if not defined, else use the provided stuff
        if data is None:
            data = self.data
            labels = self.labels
        else:
            labels = self.labels

        # Use info gain for classification as we have a binary classification problem
        info = mutual_info_classif(data, labels, discrete_features=False)

        # Create data frame with feature names and sort ascending
        combined = list(zip(self.df.columns, info))
        combined = pd.DataFrame(combined, columns=['Feature Name', 'Info Gain'])

        # Sort ascending and reindex
        combined = combined.sort_values(by=['Info Gain'], ascending=False)
        combined.index = range(1, len(self.df.columns) + 1)

        # print("Information gain of whole dataset")
        # print(combined)

        return combined

    def repeat_info_gain(self, data, repeats):
        result_df = pd.DataFrame()
        for i in range(repeats):
            if i == 0:
                result_df = self.information_gain(data)
            else:
                result_df = pd.merge(result_df, self.information_gain(data), on='Feature Name')

        # Compute mean and sort
        result_df['Mean'] = result_df.mean(axis=1)

        result_df = result_df.sort_values(by=['Mean'], ascending=False)
        result_df.index = range(1, len(self.df.columns) + 1)

        return result_df

    def chi2_stats(self, data=None):
        # Use data from class if not defined, else use the provided stuff
        if data is None:
            data = self.data
            labels = self.labels
        else:
            labels = self.labels

        pvals = chi2(data, labels)

        print("Chi2 stats of whole dataset")
        print(pvals)

        return pvals

    def standard_scaling(self):
        # Scale features to N(0,1) -> xi - mean(x) / std(x)
        # THIS ASSUME THAT THE DATA IS NORMAL DISTRIBUTED!!
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(self.data, self.labels)

        return scaled_features

    def minmax_scaling(self):
        # Scale features to predetermined range (0-1) -> xi - min(x) / max(x) - min(x)
        scaler = MinMaxScaler()
        scaled_features = scaler.fit_transform(self.data, self.labels)

        return scaled_features

    def robust_scaling(self):
        # Scale just like minmax but more robust against outliers
        scaler = RobustScaler()
        scaled_features = scaler.fit_transform(self.data, self.labels)

        return scaled_features

    def _get_clf_attributes(self, val):
        try:
            # Deconstruct classifiers settings
            clf = val['clf']
            name = val['name']

            return clf, name
        except Exception as e:
            raise e

    def _get_optimized_clf(self, val):
        # Make sure that the classifier is defined
        try:
            classifier, name = self._get_clf_attributes(val)
        except ValueError as e:
            print(e)
            return None

        # Fail fast if model or param not available
        if 'optimized_model' not in val and 'optimized_param' not in val:
            print("Classifier {} not optimized, first call .optimize() or define optimized_param.".format(name))
            return None

        # Check if optimized classifier is available
        if 'optimized_model' in val:
            clf = val['optimized_model']

        if 'optimized_param' in val:
            params = val['optimized_param']
            clf = classifier.set_params(**params)

        return clf, name

    def optimize(self, metric='f1'):
        print("-- Start optimizing by grid search --")
        for _, val in enumerate(self.classifiers):
            # Make sure that the classifier is defined
            try:
                clf, name = self._get_clf_attributes(val)

                # We also need the optimization grid
                grid = val['grid']
            except Exception as e:
                print(e)
                continue

            print("Optimizing: {}".format(name))

            # Do a grid search with 10 folds
            optimize_cv = KFold(n_splits=10, shuffle=True)
            clf = GridSearchCV(estimator=clf, param_grid=grid, cv=optimize_cv, scoring=metric, n_jobs=-2)
            clf.fit(self.data, self.labels)
            params = clf.best_params_

            print("Optimal settings {}:".format(name))
            print(params)

            # Save the results
            val['optimized_param'] = params
            val['optimized_model'] = clf.best_estimator_

        print("-- Finished optimizing -- ")

    def cross_val(self):
        print("-- Cross validation with 10-folds --")
        for _, val in enumerate(self.classifiers):
            # Get optimized classifier
            clf, name = self._get_optimized_clf(val)

            # Skip this one if it was not available
            if clf is None:
                continue

            # Now check performance of the classifier with cross validation
            test_cv = KFold(n_splits=10, shuffle=True)
            performance = cross_validate(estimator=clf, X=self.data, y=self.labels, scoring=metrics, cv=test_cv,
                                         n_jobs=-2)

            print("Cross validation performance {}:".format(name))
            self.__cv_report(performance)

        print("-- Finished cross validation --")

    def __split_cv_results(self, results):
        train = dict()
        test = dict()

        # Average metrics and split
        for k, v in results.items():
            if 'train' in k:
                train[k] = v.mean()
            if 'test' in k:
                test[k] = v.mean()

        return train, test

    def __cv_report(self, results):
        train, test = self.__split_cv_results(results)

        tr = pd.Series(data=train)
        tst = pd.Series(data=test)

        print("TRAIN")
        print(tr.to_string())
        print("\nTEST")
        print(tst.to_string())
        print("\n")

    def __test_report(self, y_true, y_preds, y_probs):
        # Compute metrics
        report = classification_report(y_true=y_true, y_pred=y_preds, target_names=classnames)
        auc = roc_auc_score(y_true=y_true, y_score=y_preds)
        auc_prob = roc_auc_score(y_true=y_true, y_score=y_probs[:, 1])
        conf = confusion_matrix(y_true=y_true, y_pred=y_preds, labels=[0, 1])

        print(report)
        print("AUC on binary labels: {}".format(auc))
        print("AUC on probabilities: {}".format(auc_prob))
        print("Confusion matrix:")
        print(conf)
        print("\n")

    def test(self):
        print("-- Performance on split: 70% train - 30% split --")
        for _, val in enumerate(self.classifiers):
            # Get optimized classifier
            clf, name = self._get_optimized_clf(val)

            # Skip this one if it was not available
            if clf is None:
                continue

            # Split the data 80/30 in trn/tst
            trn, tst, trn_label, tst_label = train_test_split(self.data, self.labels, test_size=0.3, shuffle=True)

            # Train classifier
            clf.fit(trn, trn_label)

            # Make predictions with the model
            y_preds = clf.predict(tst)
            y_proba = clf.predict_proba(tst)

            # Output the results
            print("Test performance: {}".format(name))
            self.__test_report(tst_label, y_preds, y_proba)

        print("-- Finished test reports --")
