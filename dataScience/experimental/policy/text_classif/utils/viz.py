import matplotlib.pyplot as plt
import numpy as np


def plot_sg_results(results, data_name=None, save=False, show=True):
    """
    Shamelessly stolen

    Args:
        results (list): tuples `(classifier_name, accuracy_score,
                                 train_time, test_dat)`

        data_name (str): label for the data set

        save (bool): if True, save the plot using the `data_name`

        show (bool): If True, show the plot

    Returns:
        None

    """
    if data_name is None:
        data_name = ""
    indices = np.arange(len(results))

    results = [[x[i] for x in results] for i in range(4)]

    clf_names, score, training_time, test_time = results
    clf_names = [str(clf).split("(")[0] for clf in clf_names]

    training_time = np.array(training_time) / np.max(training_time)
    test_time = np.array(test_time) / np.max(test_time)

    plt.figure(figsize=(12, 8))
    plt.title(data_name)
    plt.barh(indices, score, 0.2, label="accuracy", color="navy")
    plt.barh(
        indices + 0.3, training_time, 0.2, label="training time", color="c"
    )
    plt.barh(
        indices + 0.6, test_time, 0.2, label="test time", color="darkorange"
    )
    plt.yticks(())
    plt.legend(loc="best")
    plt.subplots_adjust(left=0.25)
    plt.subplots_adjust(top=0.95)
    plt.subplots_adjust(bottom=0.05)

    for i, c in zip(indices, clf_names):
        plt.text(-0.3, i, c)
    plt.grid(True)

    if save:
        fig_name = data_name.replace(" ", "-")
        plt.savefig(fig_name, dpi=300)
    if show:
        plt.show()
    plt.close()
