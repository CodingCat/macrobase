import argparse
import json
from matplotlib import patches
import math
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import numpy as np
import os
from common import add_plot_limit_args
from common import set_plot_limits
import pandas as pd
from plot_distribution import _plot_hist2d
from algebra import get_ellipse_from_covariance

SAVEFIG_INFER_VALUE = 'INFER_SAVEFIG_FILENAME'


def parse_args(*argument_list):
  parser = argparse.ArgumentParser()
  parser.add_argument('--test-class', default='VariationalGMMTest')
  parser.add_argument('--test-method',
                      default='bivariateOkSeparatedNormalTest')
  parser.add_argument('--scored-grid',
                      default='target/scores/3gaussians-7k-grid.json')
  parser.add_argument('--score-cap', type=float)
  parser.add_argument('--plot', default='density',
                      choices=['density', 'components', 'difference', 'noop'])
  # histogram
  parser.add_argument('--hist2d', nargs=2)
  parser.add_argument('--histogram-bins', type=int, default=100)
  parser.add_argument('--csv', type=argparse.FileType('r'))
  # centers
  parser.add_argument('--centers', type=argparse.FileType('r'))
  parser.add_argument('--weights', type=argparse.FileType('r'))
  parser.add_argument('--covariances', type=argparse.FileType('r'))
  parser.add_argument('--savefig', nargs='?', const=SAVEFIG_INFER_VALUE)
  add_plot_limit_args(parser)
  args = parser.parse_args(*argument_list)
  return args


def load_json_dump(filename):
  with open(filename) as infile:
    data = json.load(infile)
  X, Y, Z = [], [], []
  for point in data:
    x, y = point['metrics']['data']
    X.append(x)
    Y.append(y)
    Z.append(point['score'])
  return X, Y, Z


def load_cluster_parameters(filename):
  if type(filename) is str:
    with open(filename) as infile:
      data = json.load(infile)
  else:
    data = json.load(filename)
  return [p['data'] for p in data]


def plot_score_contours(args):
  if args.centers and args.covariances and args.weights:
    # normalize weights to sum to 1.
    weights = json.load(args.weights)
    weights = [w / sum(weights) for w in weights]
    print weights
    weights = [0.4 * w / max(weights) for w in weights]
    print weights
    centers = load_cluster_parameters(args.centers)
    sigmas = load_cluster_parameters(args.covariances)
    fig = plt.figure(0)
    ax = fig.add_subplot(111, aspect='equal')
    for i in range(len(centers)):
      w, h, angle = get_ellipse_from_covariance(sigmas[i])
      e = patches.Ellipse(centers[i], w, h, angle=angle)
      e.set_alpha(weights[i])
      ax.add_artist(e)
    x, y = zip(*centers)
    plt.scatter(x, y, s=weights)

  X, Y, Z = load_json_dump(args.scored_grid)

  if args.score_cap:
    Z = [min(z, args.score_cap) for z in Z]

  minX, maxX = min(X), max(X)
  minY, maxY = min(Y), max(Y)

  size = int(math.sqrt(len(Z)))
  X = np.reshape(X, (size, size))
  Y = np.reshape(Y, (size, size))
  Z = np.reshape(Z, (size, size))

  try:
    means = load_cluster_parameters('target/scores/{0.test_class}-{0.test_method}-means.json'.format(args))  # noqa
    sigmas = load_cluster_parameters('target/scores/{0.test_class}-{0.test_method}-covariances.json'.format(args))  # noqa
    with open('target/scores/{0.test_class}-{0.test_method}-weights.json'.format(args)) as infile:  # noqa
      weights = json.load(infile)

    # normalize weights to sum to 1.
    weights = [w / sum(weights) for w in weights]
  except:
    pass


  def format_args(i):
    kwargs = {}
    kwargs['mux'] = means[i][0]
    kwargs['muy'] = means[i][1]
    kwargs['sigmax'] = math.sqrt(sigmas[i][0][0])
    kwargs['sigmay'] = math.sqrt(sigmas[i][1][1])
    kwargs['sigmaxy'] = sigmas[i][0][1]
    return kwargs

  Zgaussians = weights[0] * mlab.bivariate_normal(X, Y, **format_args(0))
  for i in range(1, len(means)):
    Zgaussians += weights[i] * mlab.bivariate_normal(X, Y, **format_args(i))

  if args.plot == 'components':
    CS = plt.contour(X, Y, Zgaussians, linewidth=10000, inline=1)
  elif args.plot == 'density':
    CS = plt.contour(X, Y, Z, linewidth=10000, inline=1)
  elif args.plot == 'difference':
    CS = plt.contour(X, Y, Z - Zgaussians, linewidth=10000, inline=1)

  if args.plot != 'noop':
    #plt.clabel(CS, inline=1)
    pass

  set_plot_limits(plt, args)

  if args.csv and args.hist2d:
    args.data = pd.read_csv(args.csv)
    _plot_hist2d(args.data, args)

  if args.savefig:
    if args.savefig == SAVEFIG_INFER_VALUE:
      name = os.path.basename(args.scored_grid).rsplit('.')[0]
      filename = 'target/plots/{}.png'.format(name)
    else:
      filename = args.savefig
    print 'saving figure to - ', filename
    plt.savefig(filename, dpi=320)
  else:
    plt.show()


if __name__ == '__main__':
  # XX, YY, ZZ = load_json_dump('target/scores/3gaussians-7k-data.json')
  # plt.hist2d(XX, YY, bins=60)
  args = parse_args()
  plot_score_contours(args)
