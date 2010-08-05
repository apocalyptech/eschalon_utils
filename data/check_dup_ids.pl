#!/usr/bin/perl
# vim: set expandtab tabstop=4 shiftwidth=4:

use strict;
use warnings;

my $file;
my $line;
my $df;
my $id;
my %seen = ();
my @okaypatterns = qw(
    ^hbox\d+$
    ^alignment\d+$
    ^scroll\d+$
    ^label\d+$
    ^button\d+$
    ^table\d+$
    ^vbox\d+$
    ^cellrenderertext\d+$
    ^viewport\d+$
    ^image\d+$
    ^scrolledwindow\d+$
    ^dialog-vbox\d+$
    ^dialog-action_area\d+$
    );
my $pat;
while ($file = shift)
{
    open $df, $file or die "couldn't open $file";
    FILELOOP: while ($line = <$df>)
    {
        chomp $line;
        if ($line =~ / id="(.*?)"/)
        {
            $id = $1;
            if ($line =~ /<col id="/)
            {
                next FILELOOP;
            }
            foreach $pat (@okaypatterns)
            {
                if ($id =~ /$pat/)
                {
                    next FILELOOP;
                }
            }
            if (exists($seen{$id}))
            {
                print "$file - already seen ID $id\n";
            }
            $seen{$id} = 1;
        }
    }
    close $df;
}
