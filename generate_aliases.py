#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
import itertools
import os.path
import sys

try:
    xrange  # Python 2
except NameError:
    xrange = range  # Python 3


def main():
    # (alias, full, allow_when_oneof, incompatible_with)
    cmds = [
        ('k', 'kubectl', None, ['wk']),
        ('wk', 'watch kubectl', None, ['k', 'oyaml', 'ojson', 'owide']),
    ]

    globs = [
        ('sys', '--namespace=kube-system', None, ['sys', 'm']),
        ('m', '--namespace=management', None, ['m', 'sys'])
    ]

    ops = [
        ('a', 'apply --recursive -f', None, ['wk']),
        ('ak', 'apply -k', None, ['sys', 'm', 'wk']),
        ('k', 'kustomize', None, ['sys', 'm', 'wk']),
        ('ex', 'exec -i -t', None, ['wk']),
        ('lo', 'logs -f', None, ['wk']),
        ('lop', 'logs -f -p', None, ['wk']),
        ('p', 'proxy', None, ['sys', 'm','wk']),
        ('pf', 'port-forward', None, ['sys', 'm','wk']),
        ('g', 'get', None, None),
        ('d', 'describe', None, ['wk']),
        ('rm', 'delete', None, ['wk']),
        ('e', 'edit', None, ['wk']),
        ('run', 'run --rm --restart=Never --image-pull-policy=IfNotPresent -i -t', None, ['wk']),
    ]

    res = [
        ('po', 'pods', ['g', 'd', 'rm'], None),
        ('dep', 'deployment', ['g', 'd', 'rm'], None),
        ('st', 'statefulset', ['g', 'd', 'rm'], None),
        ('ds', 'daemonset', ['g', 'd', 'rm'], None),
        ('svc', 'service', ['g', 'd', 'rm'], None),
        ('ing', 'ingress', ['g', 'd', 'rm'], None),
        ('cm', 'configmap', ['g', 'd', 'rm'], None),
        ('sec', 'secret', ['g', 'd', 'rm'], None),
        ('pvc', 'persistentvolumeclaim', ['g', 'd', 'rm'], None),
        ('pv', 'persistentvolume', ['g', 'd', 'rm'], ['sys', 'm']),
        ('no', 'nodes', ['g', 'd'], ['sys', 'm']),
        ('ns', 'namespaces', ['g', 'd', 'rm'], ['sys', 'm']),
        ('gr', 'gitrepository', ['g', 'd', 'rm'], None),
        ('h', 'helmrepository', ['g', 'd', 'rm'], None),
        ('hr', 'helmrelease', ['g', 'd', 'rm', 'r', 're', 's'], None),
        ('k', 'kustomization', ['g', 'd', 'rm', 'r', 're', 's'], None),
        ('ss', 'secretstore', ['g', 'd', 'rm'], None),
        ('es', 'externalsecret', ['g', 'd', 'rm'], None),
        ('ces', 'clusterexternalsecret', ['g', 'd', 'rm'], ['sys', 'm']),
        ('css', 'clustersecretstore', ['g', 'd', 'rm'], ['sys', 'm']),
    ]
    res_types = [r[0] for r in res]

    args = [
        ('oyaml', '-o=yaml', ['g'], ['owide', 'ojson', 'sl']),
        ('owide', '-o=wide', ['g'], ['oyaml', 'ojson']),
        ('ojson', '-o=json', ['g'], ['owide', 'oyaml', 'sl']),
        ('all', '--all-namespaces', ['g', 'd'], ['rm', 'no', 'sys']),
        ('sl', '--show-labels', ['g'], ['oyaml', 'ojson'] + diff(res_types, ['po', 'dep'])),
        ('all', '--all', ['rm'], None), # caution: reusing the alias
        ]

    # these accept a value, so they need to be at the end and
    # mutually exclusive within each other.
    positional_args = [
        ('f', '--recursive -f', ['g', 'd', 'rm'], res_types + ['all', 'l', 'sys', 'm']),
        ('l', '-l', ['g', 'd', 'rm'], ['all']),
        ('n', '--namespace', ['g', 'd', 'rm','lo', 'ex', 'pf'], ['ns', 'no', 'sys', 'm', 'all', 'ces', 'css'])
    ]

    # [(part, optional, take_exactly_one)]
    parts = [
        (cmds, False, True),
        (globs, True, False),
        (ops, True, True),
        (res, True, True),
        (args, True, False),
        (positional_args, True, True),
        ]

    out = gen(parts)
    out = filter(is_valid, out)

    # prepare output
    if not sys.stdout.isatty():
        header_path = \
            os.path.join(os.path.dirname(os.path.realpath(__file__)), 'license_header')
        with open(header_path, 'r') as f:
            print(f.read())
    for cmd in out:
        print("alias {}='{}'".format(''.join([a[0] for a in cmd]), ' '.join([a[1] for a in cmd])))


def gen(parts):
    out = [()]
    for (items, optional, take_exactly_one) in parts:
        orig = list(out)
        combos = []

        if optional and take_exactly_one:
            combos = combos.append([])

        if take_exactly_one:
            combos = combinations(items, 1, include_0=optional)
        else:
            combos = combinations(items, len(items), include_0=optional)

        # permutate the combinations if optional (args are not positional)
        if optional:
            new_combos = []
            for c in combos:
                new_combos += list(itertools.permutations(c))
            combos = new_combos

        new_out = []
        for segment in combos:
            for stuff in orig:
                new_out.append(stuff + segment)
        out = new_out
    return out


def is_valid(cmd):
    for i in xrange(0, len(cmd)):

        # check at least one of requirements are in the cmd
        requirements = cmd[i][2]
        if requirements:
            found = False
            for r in requirements:
                for j in xrange(0, i):
                    if cmd[j][0] == r:
                        found = True
                        break
                if found:
                    break
            if not found:
                return False

        # check none of the incompatibilities are in the cmd
        incompatibilities = cmd[i][3]
        if incompatibilities:
            found = False
            for inc in incompatibilities:
                for j in xrange(0, i):
                    if cmd[j][0] == inc:
                        found = True
                        break
                if found:
                    break
            if found:
                return False

    return True


def combinations(a, n, include_0=True):
    l = []
    for j in xrange(0, n + 1):
        if not include_0 and j == 0:
            continue
        l += list(itertools.combinations(a, j))
    return l


def diff(a, b):
    return list(set(a) - set(b))


if __name__ == '__main__':
    main()
