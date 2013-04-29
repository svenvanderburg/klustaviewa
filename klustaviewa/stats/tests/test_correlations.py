"""Unit tests for stats.correlations module."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import os

import numpy as np

from klustaviewa.stats.cache import CacheMatrix
from klustaviewa.stats.correlations import compute_correlations, normalize
from klustaviewa.stats.tools import matrix_of_pairs
from klustaviewa.io.tests.mock_data import (setup, teardown,
                            nspikes, nclusters, nsamples, nchannels, fetdim)
from klustaviewa.io.loader import KlustersLoader
from klustaviewa.io.tools import get_array
from klustaviewa.control.controller import Controller


# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------
def load():
    # Open the mock data.
    dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                '../../io/tests/mockdata')
    xmlfile = os.path.join(dir, 'test.xml')
    l = KlustersLoader(xmlfile)
    c = Controller(l)
    return (l, c)


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------
def test_compute_correlations():
    
    n = 1000
    nspikes = 3 * n
    clusters = np.repeat([0, 1, 2],  n)
    features = np.zeros((nspikes, 2))
    masks = np.ones((nspikes, 2))
    
    # clusters 0 and 1 are close, 2 is far away from 0 and 1
    features[:n, :] = np.random.randn(n, 2)
    features[n:2*n, :] = np.random.randn(n, 2)
    features[2*n:, :] = np.array([[10, 10]]) + np.random.randn(n, 2)
    
    # compute the correlation matrix
    correlations = compute_correlations(features, clusters, masks)
    matrix = matrix_of_pairs(correlations)
    
    # check that correlation between 0 and 1 is much higher than the
    # correlation between 2 and 0/1
    assert matrix[0,1] > 100 * matrix[0, 2]
    assert matrix[0,1] > 100 * matrix[1, 2]
    
def test_recomputation_correlation():
    l, c = load()
    
    clusters_unique = l.get_clusters_unique()
    
    # Select three clusters
    clusters_selected = [2, 4, 6]
    spikes = l.get_spikes(clusters=clusters_selected)
    # cluster_spikes = l.get_clusters(clusters=clusters_selected)
    # Select half of the spikes in these clusters.
    spikes_sample = spikes[::2]
    
    # Get the correlation matrix parameters.
    features = get_array(l.get_features('all'))
    masks = get_array(l.get_masks('all', full=True))
    clusters0 = get_array(l.get_clusters('all'))
    clusters_all = l.get_clusters_unique()
    
    correlation_matrix = CacheMatrix()
    correlations0 = compute_correlations(features, clusters0, masks)
    correlation_matrix.update(clusters_unique, correlations0)
    matrix0 = normalize(correlation_matrix.to_array().copy())
    
    
    
    # Merge these clusters.
    action, output = c.merge_clusters(clusters_selected)
    cluster_new = output['to_select']
    
    # Compute the new matrix
    correlation_matrix.invalidate([2, 4, 6, cluster_new])
    clusters1 = get_array(l.get_clusters('all'))
    correlations1 = compute_correlations(features, clusters1, masks,#)
        [cluster_new])
    correlation_matrix.update([cluster_new], correlations1)
    matrix1 = normalize(correlation_matrix.to_array().copy())
    
    # print correlations0.keys()
    # print correlations1.keys()
    
    # for key in correlations0.keys():
        # if key[0] not in [2, 4, 6, 7] and key[1] not in [2, 4, 6, 7]:
            # # print key, correlations0[key], correlations1[key]
            # assert np.allclose(correlations0[key], correlations1[key]), key
    
    # Undo.
    assert c.can_undo()
    action, output = c.undo()
    
    
    # Compute the new matrix
    correlation_matrix.invalidate([2, 4, 6, cluster_new])
    clusters2 = get_array(l.get_clusters('all'))
    correlations2 = compute_correlations(features, clusters2, masks,#)
        clusters_selected)
    correlation_matrix.update(clusters_selected, correlations2)
    matrix2 = normalize(correlation_matrix.to_array().copy())
    
    assert np.array_equal(clusters0, clusters2)
    assert np.array_equal(matrix0, matrix2)
    