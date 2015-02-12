#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert stacked information into flame graph
Attributes:

Google Python Style Guide:
    http://google-styleguide.googlecode.com/svn/trunk/pyguide.html
"""
__copyright__ = "Zhaoyu Luo"

import sys
import copy
import pdb


class StackTree(object):
    def __init__(self, lines):
        """
        Args:
            lines: [line, line, line]
                line: "stacks value" e.g., unix`0xfffffffffb800c86;genunix`syscall_mstate 139"
                stack is separated by ;
        """
        self.tree = {'__meta__': {
            'value': 0,
            'depth': 0,
            'name': 'root'
            }
        }
        for line in lines:
            try:
                stacks, value = line.strip().split()
                value = int(value)
                cursor = self.tree
                cursor['__meta__']['value'] += value
                for stack in stacks.split(';'):
                    if stack in cursor:
                        cursor[stack]['__meta__']['value'] += value
                    else:
                        cursor[stack] = {
                                '__meta__': {
                                        'value': value,
                                        'depth': cursor['__meta__']['depth'] + 1,
                                        'name': stack,
                                        'parent': cursor,
                                    }
                                }
                    cursor = cursor[stack]
            except ValueError:
                print "A malformed line found: %s" % line

    def __str__(self):
        import pprint
        return pprint.pformat(self.tree)

    def _get_children(self, tree):
        return [tree[i] for i in tree if i != '__meta__']

    def _output_cmd(self, name, length, empty=0):
        sys.stdout.write(empty * ' ')
        if length == 0:
            output = ''
        elif length < 10:
            output = "%s%s" % (length, '.' * (length - 1))
        else:
            if length > (len(name) + 5):
                output = "[%s%3i%s]" % (name, length, '#' * (length - len(name) - 5))
            else:
                output = '[%s...%s]' % (name[:(length - 7)], length)
        assert len(output) == length
        sys.stdout.write(output)

    def to_flame(self):
        """
        Output max width is set as 200
        """
        flame_tree = copy.deepcopy(self.tree)
        cursor = flame_tree
        queue = self._get_children(cursor)
        line_cursor = 0
        current_depth = queue[0]['__meta__']['depth']
        while queue:
            t = queue.pop(0)
            t_value = t['__meta__']['value']
            #: zoom in
            t_value = 200 * t_value / flame_tree['__meta__']['value']
            if t['__meta__']['depth'] != current_depth:
                try:
                    assert current_depth < t['__meta__']['depth']
                except:
                    pdb.set_trace()
                print '\n'
                # align with parent
                empty = t['__meta__']['parent']['__meta__']['print_start']
                self._output_cmd(t['__meta__']['name'], t_value, empty)
                line_cursor = empty + t_value
                t['__meta__']['print_start'] = empty
                current_depth = t['__meta__']['depth']
            else:
                empty = max(t['__meta__']['parent']['__meta__'].get('print_start', 0), line_cursor) - line_cursor
                self._output_cmd(t['__meta__']['name'], t_value, empty)
                t['__meta__']['print_start'] = line_cursor + empty
                line_cursor += empty + t_value
            queue.extend(self._get_children(t))


def main():
    """Main function only in command line"""
    from sys import argv
    lines = None
    with open(argv[1], 'r') as f:
        lines = f.readlines()
    s = StackTree(lines)
    s.to_flame()


if __name__ == '__main__':
    main()
