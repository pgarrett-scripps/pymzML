#!/usr/bin/env python

import os

import pymzml


def main():
    """
    This function shows how to plot a simple spectrum. It can be directly
    plotted via this script or using the python console.

    usage:

        ./plot_spectrum.py

    """

    example_file = os.path.join(
        os.path.dirname(__file__), os.pardir, "tests", "data", "example.mzML"
    )
    run = pymzml.run.Reader(example_file)
    p = pymzml.plot.Factory()
    for spec in run:
        p.new_plot()
        p.add(spec.peaks("centroided"), color=(0, 0, 0), style="sticks", name="peaks")
        filename = "example_plot_{}_{}.html".format(
            os.path.basename(example_file), spec.ID
        )
        p.save(
            filename=filename,
            layout={
                "xaxis": {
                    "ticks": "outside",
                    "ticklen": 2,
                    "tickwidth": 0.25,
                    "showgrid": False,
                    "linecolor": "black",
                },
                "yaxis": {
                    "ticks": "outside",
                    "ticklen": 2,
                    "tickwidth": 0.25,
                    "showgrid": False,
                    "linecolor": "black",
                },
                "plot_bgcolor": "rgba(255, 255, 255, 0)",
                "paper_bgcolor": "rgba(255, 255, 255, 0)",
            },
        )
        print(f"Plotted file: {filename}")
        break


if __name__ == "__main__":
    main()
