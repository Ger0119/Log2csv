#!usr/bin/perl

use warnings;

yoko2tate($ARGV[0]);

sub yoko2tate{
    my $file  = shift;
    my @after = ();
    my $max   = 0;
    my $flag  = 0;
    my $cnt   = 0;

    open FILE,$file;
    foreach my $line(<FILE>){
        chomp($line);
        $cnt += 1;
        my @data = split(',',$line);
        if($flag == 0){
            @after = @data;
            foreach(@after){
                $_ .= ",";
            }
            $max   = @data;
            $flag  = 1;
            next;
        }
        if($max == scalar(@data)){
            foreach(0..$max-1){
                $after[$_] .= $data[$_].',';
            }
        }elsif($max > scalar(@data)){
            foreach(0..scalar(@after)-1){
                if($_ <= scalar(@data)-1){
                    $after[$_] .= $data[$_].',';
                }else{
                    $after[$_] .= ',';
                }
            }
        }else{
            foreach my $n(0..scalar(@data)-1){
                if($n < $max){
                    $after[$n] .= $data[$n].',';
                }else{
                    push @after,"";
                    foreach(0..$cnt-2){
                        $after[$n] .= ',';
                    }
                    $after[$n] .= $data[$n].',';
                }
            }
            $max = @data;
        }
    }
    close FILE;

    open  Output,">$file";
    print Output join("\n",@after);
    close Output;
}
