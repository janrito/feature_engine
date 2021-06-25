import pandas as pd
import pytest
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import NotFittedError
from sklearn.model_selection import KFold, StratifiedKFold

from feature_engine.selection import SmartCorrelatedSelection


@pytest.fixture(scope="module")
def df_single():
    # create array with 4 correlated features and 2 independent ones
    X, y = make_classification(
        n_samples=1000,
        n_features=6,
        n_redundant=2,
        n_clusters_per_class=1,
        weights=[0.50],
        class_sep=2,
        random_state=1,
    )

    # trasform array into pandas df
    colnames = ["var_" + str(i) for i in range(6)]
    X = pd.DataFrame(X, columns=colnames)

    return X, y


@pytest.fixture(scope="module")
def df_double():
    # create array with 8 correlated features and 4 independent ones
    X, y = make_classification(
        n_samples=1000,
        n_features=12,
        n_redundant=4,
        n_clusters_per_class=1,
        weights=[0.50],
        class_sep=2,
        random_state=1,
    )

    # transform array into pandas df
    colnames = ["var_" + str(i) for i in range(12)]
    X = pd.DataFrame(X, columns=colnames)

    return X, y


def test_model_performance_single_corr_group(df_single):
    X, y = df_single

    transformer = SmartCorrelatedSelection(
        variables=None,
        method="pearson",
        threshold=0.8,
        missing_values="raise",
        selection_method="model_performance",
        estimator=RandomForestClassifier(n_estimators=10, random_state=1),
        scoring="roc_auc",
        cv=3,
    )

    Xt = transformer.fit_transform(X, y)

    # expected result
    df = X[["var_0", "var_2", "var_3", "var_4", "var_5"]].copy()

    # test init params
    assert transformer.method == "pearson"
    assert transformer.threshold == 0.8
    assert transformer.variables is None
    assert transformer.missing_values == "raise"
    assert transformer.selection_method == "model_performance"
    assert transformer.scoring == "roc_auc"
    assert transformer.cv == 3

    # test fit attrs
    assert transformer.variables_ == [
        "var_0",
        "var_1",
        "var_2",
        "var_3",
        "var_4",
        "var_5",
    ]
    assert transformer.correlated_feature_sets_ == [{"var_1", "var_2"}]
    assert transformer.features_to_drop_ == ["var_1"]
    # test transform output
    pd.testing.assert_frame_equal(Xt, df)


def test_model_performance_2_correlated_groups(df_double):
    X, y = df_double

    transformer = SmartCorrelatedSelection(
        variables=None,
        method="pearson",
        threshold=0.8,
        missing_values="raise",
        selection_method="model_performance",
        estimator=RandomForestClassifier(n_estimators=10, random_state=1),
        scoring="roc_auc",
        cv=3,
    )

    Xt = transformer.fit_transform(X, y)

    # expected result
    df = X[
        ["var_0", "var_1", "var_2", "var_3", "var_5", "var_7", "var_10", "var_11"]
    ].copy()

    # test fit attrs
    assert transformer.correlated_feature_sets_ == [
        {"var_0", "var_8"},
        {"var_4", "var_6", "var_7", "var_9"},
    ]
    assert transformer.features_to_drop_ == [
        "var_4",
        "var_6",
        "var_8",
        "var_9",
    ]
    # test transform output
    pd.testing.assert_frame_equal(Xt, df)


def test_error_if_select_model_performance_and_y_is_none(df_single):
    X, y = df_single

    transformer = SmartCorrelatedSelection(
        variables=None,
        method="pearson",
        threshold=0.8,
        missing_values="raise",
        selection_method="model_performance",
        estimator=RandomForestClassifier(n_estimators=10, random_state=1),
        scoring="roc_auc",
        cv=3,
    )

    with pytest.raises(ValueError):
        transformer.fit(X)


def test_variance_2_correlated_groups(df_double):
    X, y = df_double

    transformer = SmartCorrelatedSelection(
        variables=None,
        method="pearson",
        threshold=0.8,
        missing_values="raise",
        selection_method="variance",
        estimator=None,
    )

    Xt = transformer.fit_transform(X, y)

    # expected result
    df = X[
        ["var_1", "var_2", "var_3", "var_5", "var_7", "var_8", "var_10", "var_11"]
    ].copy()

    assert transformer.features_to_drop_ == [
        "var_0",
        "var_4",
        "var_6",
        "var_9",
    ]
    # test transform output
    pd.testing.assert_frame_equal(Xt, df)


def test_cardinality_2_correlated_groups(df_double):
    X, y = df_double
    X[["var_0", "var_6", "var_7", "var_9"]] = X[
        ["var_0", "var_6", "var_7", "var_9"]
    ].astype(int)

    transformer = SmartCorrelatedSelection(
        variables=None,
        method="pearson",
        threshold=0.8,
        missing_values="raise",
        selection_method="cardinality",
        estimator=None,
    )

    Xt = transformer.fit_transform(X, y)

    # expected result
    df = X[
        ["var_1", "var_2", "var_3", "var_4", "var_5", "var_8", "var_10", "var_11"]
    ].copy()

    assert transformer.features_to_drop_ == [
        "var_0",
        "var_6",
        "var_7",
        "var_9",
    ]
    # test transform output
    pd.testing.assert_frame_equal(Xt, df)


def test_automatic_variable_selection(df_double):
    X, y = df_double

    X[["var_0", "var_6", "var_7", "var_9"]] = X[
        ["var_0", "var_6", "var_7", "var_9"]
    ].astype(int)

    # add 2 additional categorical variables, these should not be evaluated by
    # the selector
    X["cat_1"] = "cat1"
    X["cat_2"] = "cat2"

    transformer = SmartCorrelatedSelection(
        variables=None,
        method="pearson",
        threshold=0.8,
        missing_values="raise",
        selection_method="cardinality",
        estimator=None,
    )

    Xt = transformer.fit_transform(X, y)

    # expected result
    df = X[
        [
            "var_1",
            "var_2",
            "var_3",
            "var_4",
            "var_5",
            "var_8",
            "var_10",
            "var_11",
            "cat_1",
            "cat_2",
        ]
    ].copy()

    assert transformer.features_to_drop_ == [
        "var_0",
        "var_6",
        "var_7",
        "var_9",
    ]
    # test transform output
    pd.testing.assert_frame_equal(Xt, df)


def test_callable_method(df_double, dummy_method):
    X, _ = df_double

    transformer = SmartCorrelatedSelection(
        variables=None,
        method=dummy_method,
        threshold=0.8,
        missing_values="raise",
        selection_method="variance",
    )

    Xt = transformer.fit_transform(X)

    # test no empty dataframe
    assert not Xt.empty

    # test fit attrs
    assert len(transformer.correlated_feature_sets_) > 0
    assert len(transformer.features_to_drop_) > 0
    assert len(transformer.variables_) > 0
    assert transformer.n_features_in_ == len(X.columns)


def test_raises_param_errors(single_argument_method):
    with pytest.raises(ValueError):
        SmartCorrelatedSelection(threshold=None)

    with pytest.raises(ValueError):
        SmartCorrelatedSelection(method="hola")

    with pytest.raises(ValueError):
        SmartCorrelatedSelection(missing_values=None)

    with pytest.raises(ValueError):
        SmartCorrelatedSelection(selection_method="random")

    with pytest.raises(ValueError):
        SmartCorrelatedSelection(
            selection_method="missing_values", missing_values="raise"
        )

    with pytest.raises(TypeError):
        SmartCorrelatedSelection(method=single_argument_method)


def test_error_if_fit_input_not_dataframe():
    with pytest.raises(TypeError):
        SmartCorrelatedSelection().fit({"Name": [1]})


def test_non_fitted_error(df_single):
    X, y = df_single
    # when fit is not called prior to transform
    with pytest.raises(NotFittedError):
        transformer = SmartCorrelatedSelection()
        transformer.transform(X)

    transformer = SmartCorrelatedSelection(
        variables=None,
        method="pearson",
        threshold=0.8,
        missing_values="raise",
        selection_method="model_performance",
        estimator=RandomForestClassifier(n_estimators=10, random_state=1),
        scoring="roc_auc",
        cv=3,
    )


def test_KFold_generators(df_test):
    X, y = df_test

    # Kfold
    sel = SmartCorrelatedSelection(
        variables=None,
        method="pearson",
        threshold=0.8,
        missing_values="raise",
        selection_method="model_performance",
        estimator=RandomForestClassifier(n_estimators=10, random_state=1),
        scoring="roc_auc",
        cv=KFold(n_splits=3),
    )
    sel.fit(X, y)
    Xtransformed = sel.transform(X)

    # test fit attrs
    assert isinstance(sel.features_to_drop_, list)
    assert all([x for x in sel.features_to_drop_ if x in X.columns])
    assert len(sel.features_to_drop_) < X.shape[1]
    assert not Xtransformed.empty
    assert all([x for x in Xtransformed.columns if x not in sel.features_to_drop_])

    # Stratfied
    sel = SmartCorrelatedSelection(
        variables=None,
        method="pearson",
        threshold=0.8,
        missing_values="raise",
        selection_method="model_performance",
        estimator=RandomForestClassifier(n_estimators=10, random_state=1),
        scoring="roc_auc",
        cv=StratifiedKFold(n_splits=3),
    )
    sel.fit(X, y)
    Xtransformed = sel.transform(X)

    # test fit attrs
    assert isinstance(sel.features_to_drop_, list)
    assert all([x for x in sel.features_to_drop_ if x in X.columns])
    assert len(sel.features_to_drop_) < X.shape[1]
    assert not Xtransformed.empty
    assert all([x for x in Xtransformed.columns if x not in sel.features_to_drop_])

    # None
    sel = SmartCorrelatedSelection(
        variables=None,
        method="pearson",
        threshold=0.8,
        missing_values="raise",
        selection_method="model_performance",
        estimator=RandomForestClassifier(n_estimators=10, random_state=1),
        scoring="roc_auc",
        cv=None,
    )
    sel.fit(X, y)
    Xtransformed = sel.transform(X)

    # test fit attrs
    assert isinstance(sel.features_to_drop_, list)
    assert all([x for x in sel.features_to_drop_ if x in X.columns])
    assert len(sel.features_to_drop_) < X.shape[1]
    assert not Xtransformed.empty
    assert all([x for x in Xtransformed.columns if x not in sel.features_to_drop_])
